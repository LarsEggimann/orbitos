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
        self._lock = threading.Lock()

        self.microstep_resolution = (
            TMCM1021._MotorTypeA.ENUM.MicrostepResolution256Microsteps
        )  # 256 microsteps per full step
        microstep_resolution = (
            256  # the enum above is only from 0 to 8, we need the value in the name
        )
        steps_per_rotation = 200  # according to TMCM1021 documentation
        self.microsteps_per_rotation = microstep_resolution * steps_per_rotation

        self._acquire_data_thread: threading.Thread | None = None
        self._acquire_data_event: threading.Event = threading.Event()
        self._acquire_data_start_stop_delay = 0.1  # seconds

    def get_motor(self) -> TMCM1021._MotorTypeA:
        with self._lock:
            if self._motor is None:
                raise ValueError("Motor not initialized. Call connect() first.")
            return self._motor

    def get_module(self) -> TMCM1021:
        with self._lock:
            if self._module is None:
                raise ValueError("Module not initialized. Call connect() first.")
            return self._module

    def get_serial_interface(self) -> ConnectionManager:
        with self._lock:
            if self._serial_interface is None:
                raise ValueError(
                    "Serial interface not initialized. Call connect() first."
                )
            return self._serial_interface

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
        self._set_max_velocity(self.settings.get().max_velocity)
        self._set_max_acceleration(self.settings.get().max_acceleration)
        logger.info(
            "Chopper wheel initialized with settings: %s",
            self.get_motor().drive_settings,
        )
        return self.get_motor().drive_settings

    def connect(self, com_port) -> None:
        interface_args = f"--interface serial_tmcl --port {com_port} --data-rate 9600"
        with self._lock:
            self._serial_interface = ConnectionManager(interface_args).connect()
            self._module = TMCM1021(self._serial_interface)
            self._motor = self._module.motors[0]
        self.get_motor().stop()
        self.get_motor().actual_position = 0
        self.state.update(
            connection_status=ConnectionStatus.CONNECTED, status=CWStatus.IDLE
        )

    def disconnect(self) -> None:
        """
        Disconnect the chopper wheel.
        """
        with self._lock:
            if self._serial_interface is not None:
                self._serial_interface.close()
                self._serial_interface = None
            self._module = None
            self._motor = None
        self.state.update(
            connection_status=ConnectionStatus.DISCONNECTED, status=CWStatus.UNKNOWN
        )
        logger.info("Chopper wheel disconnected")

    def _acquire_data(self) -> None:
        """
        Acquire data from the chopper wheel in a separate thread.
        This method runs in a loop until the event is set.
        """
        logger.info("Starting data acquisition thread for chopper wheel")
        while self._acquire_data_event.is_set():

            velocity = self.get_actual_velocity()
            angular_position = self.get_angular_position()
            timestamp = time.time()

            data = CWData(
                velocity=velocity,
                angular_position=angular_position,
                timestamp=timestamp,
            )
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

            time.sleep(0.07)

    def start_acquire_data(self) -> None:
        """
        Start acquiring data from the chopper wheel in a separate thread.
        """
        if self._acquire_data_thread is not None and self._acquire_data_thread.is_alive():
            logger.warning("Data acquisition thread is already running")
            return

        self._acquire_data_event.set()
        self._acquire_data_thread = threading.Thread(target=self._acquire_data)
        self._acquire_data_thread.start()
        logger.info("Data acquisition thread started for chopper wheel")
        time.sleep(self._acquire_data_start_stop_delay)  # wait for acquisition to start before exiting

    def stop_acquire_data(self) -> None:
        """
        Stop acquiring data from the chopper wheel.
        """
        if self._acquire_data_thread is None or not self._acquire_data_thread.is_alive():
            logger.warning("Data acquisition thread is not running")
            return
        
        time.sleep(self._acquire_data_start_stop_delay)  # wait for rotation to properly finish before stopping the data acquisition
        self._acquire_data_event.clear()
        self._acquire_data_thread.join()
        self._acquire_data_thread = None
        logger.info("Data acquisition thread stopped for chopper wheel")

    def rotate_demo(self) -> None:
        """
        Rotate the chopper wheel in a demo mode.
        """
        self.state.update(status=CWStatus.ROTATE_DEMO_RUNNING)
        logger.info("Starting demo rotation for chopper wheel")
        self.get_motor().actual_position = 0
        self.start_acquire_data()
        self.get_motor().rotate(self._to_microsteps(1.0))  # Rotate at 1 rps
        time.sleep(5)
        self.get_motor().stop()
        self.stop_acquire_data()
        self.state.update(status=CWStatus.IDLE)


    def get_actual_velocity(self) -> float:
        """
        Get the actual velocity of the chopper wheel in rps.

        Returns:
            The actual velocity in rps.
        """
        return self._from_microsteps(self.get_motor().actual_velocity)

    def get_angular_position(self) -> float:
        """
        Get the angular position of the chopper wheel in degrees.

        Returns:
            The angular position in degrees.
        """
        return self._from_microsteps(self.get_motor().actual_position) * 360

    def _angle_to_steps(self, angle: float) -> int:
        return int(angle * self.microsteps_per_rotation / 360)

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

    def _set_max_velocity(self, velocity: float) -> None:
        """
        Sets the maximum velocity of the motor.

        Args:
            velocity: The maximum velocity of the motor in rps.
        """
        self.get_motor().linear_ramp.max_velocity = self._to_microsteps(velocity)

    def _set_max_acceleration(self, acceleration: float) -> None:
        """
        Sets the maximum acceleration of the motor.

        Args:
            acceleration: The maximum acceleration of the motor in rps^2.
        """
        self.get_motor().linear_ramp.max_acceleration = self._to_microsteps(
            acceleration
        )

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
