import logging
import time
import threading
import serial.tools.list_ports

from sqlmodel import Session
from pytrinamic.connections import ConnectionManager  # type: ignore
from pytrinamic.modules import TMCM1021  # type: ignore

from src.shared.websocket_manager import WebSocketManager
from src.shared.settings_manager import SettingsManager
from src.shared.state_manager import StateManager
from src.modules.chopperwheel.models import (
    COMPort,
    CWSettings,
    CWData,
    CWDataResponse,
    CWState,
    CWStatus,
)
from src.shared.models import ConnectionStatus
from src.core.db import engine

logger = logging.getLogger()

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

class CWController:
    def __init__(
        self,
        device_name: str,
        ws_manager: WebSocketManager[CWState, CWDataResponse, CWSettings],
    ):
        logger.info("Initializing chopper wheel controller")

        self.device_name = device_name
        self.ws_manager = ws_manager

        self.settings: SettingsManager[CWSettings] = SettingsManager(
            model=CWSettings,
            device_id=1,  # hardcoded for chopper wheel since there is only one
            device_name=self.device_name,
            engine=engine,
            on_settings_update=self.ws_manager.broadcast_setting_sync,
        )

        self.state: StateManager[CWState] = StateManager(
            model=CWState,
            device_name=self.device_name,
            on_state_update=self.ws_manager.broadcast_state_sync,
        )

        self._serial_interface: ConnectionManager | None = None
        self._module: TMCM1021 | None = None
        self._motor: TMCM1021._MotorTypeA | None = None
        self._lock = threading.RLock() # allow same thread to acquire the lock multiple times, used in synchronized() decorator

        self.microstep_resolution = (
            TMCM1021._MotorTypeA.ENUM.MicrostepResolution256Microsteps
        )  # 256 microsteps per full step
        microstep_resolution = (
            256  # the enum above is only from 0 to 8, we need the value in the name
        )
        steps_per_rotation = 200  # according to TMCM1021 documentation
        self.microsteps_per_rotation = microstep_resolution * steps_per_rotation

        self._direction_modifier: int = -1 # direction modifier for the motor

        self._acquire_data_thread: threading.Thread | None = None
        self._acquire_data_event: threading.Event = threading.Event()

    def get_motor(self) -> TMCM1021._MotorTypeA:
        if self._motor is None:
            raise ValueError("Motor not initialized. Call connect() first.")
        return self._motor

    def get_module(self) -> TMCM1021:
        if self._module is None:
            raise ValueError("Module not initialized. Call connect() first.")
        return self._module

    def get_serial_interface(self) -> ConnectionManager:
        if self._serial_interface is None:
            raise ValueError(
                "Serial interface not initialized. Call connect() first."
            )
        return self._serial_interface

    @synchronized()
    def init_motor_settings(self):
        logger.info("Initializing motor settings for chopper wheel")
        self.get_motor().drive_settings.max_current = self.settings.get().max_current
        self.get_motor().drive_settings.standby_current = (
            self.settings.get().standby_current
        )
        self.get_motor().drive_settings.boost_current = (
            self.settings.get().boost_current
        )
        self.get_motor().drive_settings.microstep_resolution = self.microstep_resolution
        self.set_max_velocity(self.settings.get().max_velocity)
        self.set_max_acceleration(self.settings.get().max_acceleration)
        logger.info(
            "Chopper wheel initialized with settings: %s",
            self.get_motor().drive_settings,
        )
        return self.get_motor().drive_settings

    @synchronized()
    def connect(self, com_port) -> None:
        interface_args = f"--interface serial_tmcl --port {com_port} --data-rate 9600"
        self._serial_interface = ConnectionManager(interface_args).connect()
        self._module = TMCM1021(self._serial_interface)
        self._motor = self._module.motors[0]
        self._motor.stop()
        self._motor.actual_position = 0
        self.state.update(
            connection_status=ConnectionStatus.CONNECTED, status=CWStatus.IDLE
        )

    @synchronized()
    def disconnect(self) -> None:
        """
        Disconnect the chopper wheel.
        """
        if self._serial_interface is not None:
            self._serial_interface.disconnect()
            self._serial_interface = None
        self._module = None
        self._motor = None
        self.state.update(
            connection_status=ConnectionStatus.DISCONNECTED, status=CWStatus.UNKNOWN
        )
        logger.info("Chopper wheel disconnected")

    def __acquire_data(self) -> None:
        """
        Acquire data from the chopper wheel in a separate thread.
        This method runs in a loop until the event is set.
        """
        logger.info("Starting data acquisition thread for chopper wheel")
        test = []
        while self._acquire_data_event.is_set():

            try:
                with self._lock:  # grab the lock and keep it for both values to be retrieved
                    velocity = self._get_actual_velocity()
                    angular_position = self._get_angular_position()
                timestamp = time.time()
                test.append(timestamp)

                data = CWData(
                    velocity=velocity,
                    angular_position=angular_position,
                    timestamp=timestamp,
                )
                print(f"Acquired data: {data}")
                with Session(engine) as session:
                    session.add(data)
                    session.commit()

                self.ws_manager.broadcast_data_sync(
                    device_name=self.device_name,
                    data=CWDataResponse(
                        device_name=self.device_name,
                        velocity=[velocity],
                        angular_position=[angular_position],
                        timestamp=[timestamp],
                    )
                )
            except Exception as e:
                logger.error("Error acquiring data from chopper wheel: %s", e)
                if not self._acquire_data_event.is_set():
                    logger.info("Data acquisition event cleared, stopping thread")
                    break
            finally:
                time.sleep(1e-5)  # 100 ms sleep time

        logger.info(f"Data acquisition thread for chopper wheel stopped. Collected {len(test)} data points.")
        avg_time_between = 0.0
        for i in range(1, len(test)):
            avg_time_between += test[i] - test[i - 1]
        avg_time_between /= len(test) - 1
        logger.info(f"Average time between data points: {avg_time_between} seconds")

    def _start_acquire_data(self) -> None:
        """
        Start acquiring data from the chopper wheel in a separate thread.
        """
        if self._acquire_data_thread is not None and self._acquire_data_thread.is_alive():
            logger.warning("Data acquisition thread is already running")
            return

        self._acquire_data_event.set()
        self._acquire_data_thread = threading.Thread(target=self.__acquire_data)
        self._acquire_data_thread.start()
        logger.info("Data acquisition thread started for chopper wheel")
        # time.sleep(self._acquire_data_start_stop_delay)  # wait for acquisition to start before exiting

    def _stop_acquire_data(self) -> None:
        """
        Stop acquiring data from the chopper wheel.
        """
        if self._acquire_data_thread is None or not self._acquire_data_thread.is_alive():
            logger.warning("Data acquisition thread is not running")
            return
        
        time.sleep(0.5)  # wait for rotation to properly finish before stopping the data acquisition
        self._acquire_data_event.clear()
        self._acquire_data_thread.join()
        self._acquire_data_thread = None
        logger.info("Data acquisition thread stopped for chopper wheel")

    def rotation_demo(self) -> None:
        """
        Rotate the chopper wheel in a demo mode.
        """
        self.state.update(status=CWStatus.ROTATE_DEMO_RUNNING)
        logger.info("Starting demo rotation for chopper wheel")
        try:
            self._start_acquire_data()
            time.sleep(0.1)  # wait for acquisition to start
            self._motor_rotate(1.0)  # Rotate at 1 rps
            
            time.sleep(5)

            self._motor_stop()

        except Exception as e:
            logger.error("Error during demo rotation: %s", e)
            self.state.update(error=str(e))
        finally:
            self._stop_acquire_data()
            self.state.update(status=CWStatus.IDLE)

    def rotation_flash_beam(self) -> None:
        """
        Perform the flash beam pattern rotation with the chopper wheel.
        """
        if not self._home_position():
            logger.error("Not at home. Cannot perform flash beam.")
            self.state.update(error="Not at home. Cannot perform flash beam.")
            return

        self.state.update(status=CWStatus.PERFORMING_FLASH_BEAM)
        logger.info("Performing flash beam with chopper wheel")
        try:
            self._set_angular_position(0)  # reset position to home
            self._start_acquire_data()
            time.sleep(self.settings.get().flash_beam_delay)

            ang = self.settings.get().angle_home_sens_to_beam_pipe

            print("move by")
            self._motor_move_by(360 + ang)
            
            print("wait for target position reached")
            self._wait_for_target_position_reached()

            time.sleep(0.3) # let the wheel stabilize a bit

            print("move by negative angle")
            self._motor_move_by(-ang)

            print("wait for target position reached")
            self._wait_for_target_position_reached()

            time.sleep(0.3)  # let the wheel stabilize a bit

            if not self._home_position():
                logger.error("Caution! Wheel has not reached home position after flash!")
                self.state.update(error="Caution! Wheel has not reached home position after flash!")
            else:
                logger.info("Flash beam operation completed successfully")
                self._motor_stop()
                self._set_angular_position(0)  # reset position to home

            
        except Exception as e:
            logger.error("Error during flash beam operation: %s", e)
            self.state.update(error=str(e))
        finally:
            self._stop_acquire_data()
            self.state.update(status=CWStatus.IDLE)

    @synchronized()
    def _home_position(self) -> bool:
        """
        Check if the home position is reached.

        Returns:
            True if the home position is reached, False otherwise.
        """
        return self.get_module().get_digital_input(1) == 0

    @synchronized()
    def _get_actual_velocity(self) -> float:
        """
        Get the actual velocity of the chopper wheel in rps.

        Returns:
            The actual velocity in rps.
        """
        return self._from_microsteps(self._direction_modifier * self.get_motor().actual_velocity)

    @synchronized()
    def _get_angular_position(self) -> float:
        """
        Get the angular position of the chopper wheel in degrees.

        Returns:
            The angular position in degrees.
        """
        return self._steps_to_angle(self._direction_modifier * self.get_motor().actual_position)

    @synchronized()
    def set_max_velocity(self, velocity: float) -> None:
        """
        Sets the maximum velocity of the motor.

        Args:
            velocity: The maximum velocity of the motor in rps.
        """
        self.get_motor().linear_ramp.max_velocity = self._to_microsteps(velocity)
        if self.settings.get().max_velocity != velocity:
            self.settings.update(max_velocity=velocity)

    @synchronized()
    def set_max_acceleration(self, acceleration: float) -> None:
        """
        Sets the maximum acceleration of the motor.

        Args:
            acceleration: The maximum acceleration of the motor in rps^2.
        """
        self.get_motor().linear_ramp.max_acceleration = self._to_microsteps(
            acceleration
        )
        if self.settings.get().max_acceleration != acceleration:
            self.settings.update(max_acceleration=acceleration)

    @synchronized()
    def _set_angular_position(self, position: float) -> None:
        """
        Sets the angular position of the motor.

        Args:
            position: The angular position in degrees.
        """
        self.get_motor().actual_position = self._angle_to_steps(self._direction_modifier * position)

    @synchronized()
    def set_max_current(self, current: int) -> None:
        """
        Sets the maximum current of the motor.

        Args:
            current: The maximum current in [0-255].
        """
        self.get_motor().drive_settings.max_current = current
        self.settings.update(max_current=current)

    @synchronized()
    def set_standby_current(self, current: int) -> None:
        """
        Sets the standby current of the motor.

        Args:
            current: The standby current in [0-255].
        """
        self.get_motor().drive_settings.standby_current = current
        self.settings.update(standby_current=current)

    @synchronized()
    def set_boost_current(self, current: int) -> None:
        """
        Sets the boost current of the motor.

        Args:
            current: The boost current in [0-255].
        """
        self.get_motor().drive_settings.boost_current = current
        self.settings.update(boost_current=current)

    @synchronized()
    def _motor_rotate(self, velocity: float) -> None:
        """
        Rotate the chopper wheel at a specified velocity.

        Args:
            velocity: The velocity in rps.
        """
        self.get_motor().rotate(self._direction_modifier * self._to_microsteps(velocity))

    @synchronized()
    def _motor_move_to(self, angle: float, velocity: float | None = None) -> None:
        """
        Move the chopper wheel to a specified angle.

        Args:
            angle: The angle in degrees.
            velocity: The velocity in rps. If None, the maximum velocity is used.
        """
        v = self._to_microsteps(velocity) if velocity is not None else None
        self.get_motor().move_to(self._direction_modifier * self._angle_to_steps(angle), v)

    @synchronized()
    def _motor_move_by(self, angle: float, velocity: float | None = None) -> None:
        """
        Move the chopper wheel by a specified angle.

        Args:
            angle: The angle in degrees.
            velocity: The velocity in rps. If None, the maximum velocity is used.
        """
        v = self._to_microsteps(velocity) if velocity is not None else None
        self.get_motor().move_by(self._direction_modifier * self._angle_to_steps(angle), v)

    @synchronized()
    def _motor_stop(self) -> None:
        """
        Stop the chopper wheel.
        """
        self.get_motor().stop()

    @synchronized()
    def _motor_get_position_reached(self) -> bool:
        """
        Check if the target position is reached.

        Returns:
            True if the target position is reached, False otherwise.
        """
        return self.get_motor().get_position_reached()

    def _wait_for_target_position_reached(self) -> None:
        """
        Wait for the target position to be reached.
        This method blocks until the target position is reached.
        """
        while not self._motor_get_position_reached():
            time.sleep(0.1)

    def get_available_com_ports(self) -> list[COMPort]:
        """
        Get the available COM ports for the chopper wheel.

        Returns:
            A list of available COM ports.
        """
        com_ports = serial.tools.list_ports.comports()
        return [
            COMPort(port=port.device, description=port.description)
            for port in com_ports
        ]

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
