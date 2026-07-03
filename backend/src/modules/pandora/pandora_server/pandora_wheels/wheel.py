import logging
import time
import threading
import serial.tools.list_ports # type: ignore

from sqlmodel import Session
from pytrinamic.connections import ConnectionManager, UsbTmclInterface  # type: ignore
from pytrinamic.modules import TMCM1240  # type: ignore

from src.shared.websocket_manager import WebSocketManager
from src.shared.settings_manager import SettingsManager
from src.shared.state_manager import StateManager

from src.shared.models import ConnectionStatus
from src.core.db import engine

from ..models import PandoraState, PandoraWheelState

logger = logging.getLogger(__name__)

from src.shared.websocket_manager import WebSocketManager


# decorator to synchronize access to methods to serial interface and motor
# methods annotated with this decorator will acquire a lock before executing and keep it until the method returns
# this ensures that only one thread can access the serial interface and motor at a time AND more importantly
# waits for the connection to respond before releasing the lock
def synchronized(lock_attr="_lock"):
    def decorator(method):
        def wrapper(self, *args, **kwargs):
            lock = getattr(self, lock_attr)
            with lock:
                return method(self, *args, **kwargs)
        return wrapper
    return decorator


class Wheel():
    def __init__(self, wheel_id: int, connection_port: str, state: StateManager[PandoraState]):
        self.wheel_id = wheel_id
        self.connection_port = connection_port
        self.state = state

        # add the wheel to the state
        this_state = self.state.get()
        wheels_dict = this_state.wheels
        wheels_dict[self.wheel_id] = PandoraWheelState(
            status="unknown",
            position=None,
            velocity=None,
        )   

        self._serial_interface: UsbTmclInterface | None = None
        self._module: TMCM1240 | None = None
        self._motor: TMCM1240._MotorTypeA | None = None
        self._lock = threading.RLock()  # allow same thread to acquire the lock multiple times, used in synchronized() decorator

        self.microstep_resolution = (
            TMCM1240._MotorTypeA.ENUM.MicrostepResolution256Microsteps
        )  # 256 microsteps per full step
        microstep_resolution = (
            256  # the enum above is only from 0 to 8, we need the value in the name
        )
        steps_per_rotation = 200  # according to TMCM1240 documentation
        self.microsteps_per_rotation = microstep_resolution * steps_per_rotation

        self._direction_modifier: int = -1  # direction modifier for the motor

        self._acquire_data_thread: threading.Thread | None = None
        self._acquire_data_event: threading.Event = threading.Event()
        self._reference_search_ongoing: threading.Event = threading.Event()

        # connect and initialize settings
        try:
            self.connect(connection_port) # TODO: add failsafe retry logic here or in .connect() method

            self.get_motor().drive_settings.max_current = 60
            self.get_motor().drive_settings.standby_current = 10
            self.get_motor().drive_settings.boost_current = 60
            self.get_motor().drive_settings.microstep_resolution = self.microstep_resolution
            self.get_motor().linear_ramp.max_acceleration = 30000
            self.get_motor().linear_ramp.max_velocity = 10000
            self.get_motor().set_axis_parameter(self.get_motor().AP.RelativePositioningOption, 0) # set move_by relative to the actual position = 1, last target position = 0

            # reference search settings
            self.get_motor().set_axis_parameter(self.get_motor().AP.ReferenceSearchMode, 8) # 8 = Search home switch in negative direction, ignore end switches.
            self.get_motor().set_axis_parameter(self.get_motor().AP.ReferenceSearchSpeed, 2000) # speed for reference search in pps
            self.get_motor().set_axis_parameter(self.get_motor().AP.ReferenceSwitchSpeed, 200) # speed for reference search in pps

        except Exception as e:
            logger.error(f"Failed to connect wheel {self.wheel_id} on port {connection_port}: {e}")



    def get_motor(self) -> TMCM1240._MotorTypeA:
        if self._motor is None:
            raise ValueError("Motor not initialized. Call connect() first.")
        return self._motor

    def get_module(self) -> TMCM1240:
        if self._module is None:
            raise ValueError("Module not initialized. Call connect() first.")
        return self._module

    def get_serial_interface(self) -> UsbTmclInterface:
        if self._serial_interface is None:
            raise ValueError("Serial interface not initialized. Call connect() first.")
        return self._serial_interface
    
    @synchronized()
    def connect(self, com_port) -> None:
        interface_args = f"--interface usb_tmcl --port {com_port} --data-rate 115200"
        self._serial_interface = ConnectionManager(interface_args).connect()
        self._module = TMCM1240(self._serial_interface)
        self._motor = self._module.motors[0]
        self._motor.stop()
        self._motor.actual_position = 0
        logger.info(f"Wheel {self.wheel_id} connected on port {com_port}")

    @synchronized()
    def disconnect(self) -> None:
        if self._serial_interface is not None:
            self._serial_interface.close()
            self._serial_interface = None
        self._module = None
        self._motor = None
        self._reference_search_ongoing.clear()
        logger.info(f"Wheel {self.wheel_id} disconnected from port {self.connection_port}")

    def go_to_position(self, angle_deg: float) -> None:
        """
        Move the wheel to a specified angle.

        Args:
            angle_deg: The angle in degrees.
        """
        logger.info(f"Moving  wheel with ID {self.wheel_id} to position {angle_deg} degrees")
        self.state.get().wheels[self.wheel_id].status = "moving"
        self.state.update()
        self._motor_move_to(angle_deg)
        self._wait_for_target_position_reached()

    
    def start_reference_search(self) -> None:
        """
        Start the reference search for the wheel.
        """
        logger.info(f"Starting reference search for wheel with ID {self.wheel_id} ...")
        self._reference_search_ongoing.set()
        self.get_serial_interface().reference_search(
            command_type=0, # 0 starts the search, 1 stops the search, and 2 returns the status.
            motor=0 # motor index, in this case we have only one motor, so the index is 0
        )
        self._wait_for_target_position_reached()
        self._reference_search_ongoing.clear()
        logger.info(f"Reference search for wheel with ID {self.wheel_id} completed.")

    def stop_reference_search(self) -> None:
        """
        Stop the reference search for the wheel.
        """
        logger.info(f"Stopping reference search for wheel with ID {self.wheel_id} ...")
        self.get_serial_interface().reference_search(
            command_type=1, # 0 starts the search, 1 stops the search, and 2 returns the status.
            motor=0 # motor index, in this case we have only one motor, so the index is 0
        )
        self._reference_search_ongoing.clear()
        logger.info(f"Reference search for wheel with ID {self.wheel_id} completed.")

    @synchronized()
    def _motor_move_to(self, angle: float, velocity: float | None = None) -> None:
        """
        Move the wheel to a specified angle.

        Args:
            angle: The angle in degrees.
            velocity: The velocity in rps. If None, the maximum velocity is used.
        """
        v = self._to_microsteps(velocity) if velocity is not None else None
        self.get_motor().move_to(
            self._direction_modifier * self._angle_to_steps(angle), v
        )

    @synchronized()
    def _motor_get_position_reached(self) -> bool:
        """
        Check if the target position is reached.

        Returns:
            True if the target position is reached, False otherwise.
        """
        return self.get_motor().get_position_reached()
    
    def _update_wheel_state(self) -> None:
        curr_pos = self._get_angular_position()
        curr_vel = self._get_actual_velocity()
        if self._reference_search_ongoing.is_set():
            status = "reference_search"
        else:
            status = "moving" if abs(curr_vel) > 0.001 else "idle"
        self.state.get().wheels[self.wheel_id].status = status
        self.state.get().wheels[self.wheel_id].position = curr_pos
        self.state.get().wheels[self.wheel_id].velocity = curr_vel
        self.state.update()


    def _wait_for_target_position_reached(self) -> None:
        """
        Wait for the target position to be reached.
        This method blocks until the target position is reached.
        Send status updates to the state manager while waiting.
        """
        while not self._motor_get_position_reached():
            self._update_wheel_state()
            time.sleep(0.2)

        time.sleep(0.1) # wait a bit to make sure the motor has stopped and position is updated
        self._update_wheel_state()
    
    @synchronized()
    def _get_actual_velocity(self) -> float:
        """
        Get the actual velocity of the chopper wheel in rps.

        Returns:
            The actual velocity in rps.
        """
        return self._from_microsteps(
            self._direction_modifier * self.get_motor().actual_velocity
        )

    @synchronized()
    def _get_angular_position(self) -> float:
        """
        Get the angular position of the chopper wheel in degrees.

        Returns:
            The angular position in degrees.
        """
        return self._steps_to_angle(
            self._direction_modifier * self.get_motor().actual_position
        )
    
    @synchronized()
    def _motor_stop(self) -> None:
        """
        Stop the chopper wheel.
        """
        self.get_motor().stop()

    def _angle_to_steps(self, angle: float) -> int:
        return int(angle * self.microsteps_per_rotation / 360)

    def _steps_to_angle(self, steps: int) -> float:
        return steps * 360 / self.microsteps_per_rotation

    def _to_microsteps(self, value: float) -> int:
        """
        Converts a value in rps to microsteps.

        Args:
            value: The value in rps.

        Returns:
            The value in microsteps.
        """
        return int(value * self.microsteps_per_rotation)

    def _from_microsteps(self, value: int) -> float:
        """
        Converts a value in microsteps to rps.

        Args:
            value: The value in microsteps.

        Returns:
            The value in rps.
        """
        return value / self.microsteps_per_rotation

    def shutdown(self) -> None:
        logger.info(f"Disconnecting wheel {self.wheel_id} ...")
        self.disconnect()
