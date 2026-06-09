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

logger = logging.getLogger(__name__)

from src.shared.websocket_manager import WebSocketManager

from .wheel import Wheel

class WheelsController:
    def __init__(self, ws_manager: WebSocketManager):

        # self._wheels = dict(
        #     0: Wheel(wheel_id=0, connection_port="/dev/ttyACM0")
        #     # 1: Wheel(wheel_id=1, connection_port="/dev/ttyACM1"),
        #     # 2: Wheel(wheel_id=2, connection_port="/dev/ttyACM2"),
        #     # 3: Wheel(wheel_id=3, connection_port="/dev/ttyACM3"),
        # )
        self._wheels: dict[int, Wheel] = {
            0: Wheel(wheel_id=0, connection_port="/dev/ttyACM0"),
            # 1: Wheel(wheel_id=1, connection_port="/dev/ttyACM1"),
            # 2: Wheel(wheel_id=2, connection_port="/dev/ttyACM2"),
            # 3: Wheel(wheel_id=3, connection_port="/dev/ttyACM3"),
        }

        self.ws_manager = ws_manager

    def get_wheel(self, wheel_id: int) -> Wheel:
        if wheel_id not in self._wheels:
            raise ValueError(f"Wheel with ID {wheel_id} not found.")
        return self._wheels[wheel_id]

    def go_to_position(self, wheel_id: int, angle_deg: float):
        self.get_wheel(wheel_id).go_to_position(angle_deg)

    def start_reference_search(self, wheel_id: int):
        self.get_wheel(wheel_id).start_reference_search()

    def stop_reference_search(self, wheel_id: int):
        self.get_wheel(wheel_id).stop_reference_search()
