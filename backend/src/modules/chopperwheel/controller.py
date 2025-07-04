import logging
import time
import threading

import pyvisa
import numpy as np
from sqlmodel import Session
from pytrinamic.connections import ConnectionManager  # type: ignore
from pytrinamic.modules import TMCM1021  # type: ignore

from src.core.config import config
from src.shared.websocket_manager import WebSocketManager
from src.shared.settings_manager import SettingsManager
from src.shared.state_manager import StateManager
from src.modules.chopperwheel.models import (
    CWSettings,
    CWDataResponse,
    CWState,
    CWStatus
)
from src.shared.models import ConnectionStatus
from src.core.db import engine

logger = logging.getLogger()


class CWController:
    def __init__(
        self,
        device_name: str,
        ws_manager: WebSocketManager[
            CWState, CWDataResponse, CWSettings
        ],
    ):
        logger.info(
            "Initializing chopper wheel controller"
        )

        self.device_name = device_name
        self.ws_manager = ws_manager

        self.settings: SettingsManager[CWSettings] = SettingsManager(
            model=CWSettings,
            device_id=1, # hardcoded for chopper wheel since there is only one
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

        self.microstep_resolution = TMCM1021._MotorTypeA.ENUM.MicrostepResolution256Microsteps # 256 microsteps per full step
        microstep_resolution = 256 # the enum above is only from 0 to 8, we need the value in the name
        steps_per_rotation = 200  # according to TMCM1021 documentation

        self.microsteps_per_rotation = microstep_resolution * steps_per_rotation

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
                raise ValueError("Serial interface not initialized. Call connect() first.")
            return self._serial_interface

    def init_motor_settings(self):
        logger.info("Initializing motor settings for chopper wheel")
        self.get_motor().drive_settings.max_current = self.settings.get().max_current
        self.get_motor().drive_settings.standby_current = self.settings.get().standby_current
        self.get_motor().drive_settings.boost_current = self.settings.get().boost_current
        self.get_motor().drive_settings.microstep_resolution = self.microstep_resolution
        self._set_max_velocity(self.settings.get().max_velocity)
        self._set_max_acceleration(self.settings.get().max_acceleration)
        logger.info(
            "Chopper wheel initialized with settings: %s", self.get_motor().drive_settings
        )
        return self.get_motor().drive_settings

    def connect(self, com_port) -> None:
        interface_args = (
            f"--interface serial_tmcl --port {com_port} --data-rate 9600"
        )
        with self._lock:
            self._serial_interface = ConnectionManager(interface_args).connect()
            self._module = TMCM1021(self._serial_interface)
            self._motor = self._module.motors[0]
        self.get_motor().stop()
        self.get_motor().actual_position = 0
        self.state.update(connection_status=ConnectionStatus.CONNECTED, status=CWStatus.IDLE)

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
        self.state.update(connection_status=ConnectionStatus.DISCONNECTED, status=CWStatus.UNKNOWN)
        logger.info("Chopper wheel disconnected")

    def rotate_demo(self) -> None:
        """
        Rotate the chopper wheel in a demo mode.
        """
        self.state.update(status=CWStatus.ROTATE_DEMO_RUNNING)
        logger.info("Starting demo rotation for chopper wheel")
        self.get_motor().rotate(self._to_microsteps(1.0))  # Rotate at 1 rps
        time.sleep(5)
        self.get_motor().stop()
        self.state.update(status=CWStatus.IDLE)

    def get_actual_velocity(self) -> float:
        """
        Get the actual velocity of the chopper wheel in rps.

        Returns:
            The actual velocity in rps.
        """
        return self._from_microsteps(self.get_motor().actual_velocity)

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
        self.get_motor().linear_ramp.max_acceleration = self._to_microsteps(acceleration)
