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
from src.modules.chopperwheel.models import (
    COMPort,
    CWSettings,
    CWSettingsSet,
    CWData,
    CWDataResponse,
    CWState,
    CWStatus,
)
from src.shared.models import ConnectionStatus
from src.core.db import engine

logger = logging.getLogger(__name__)

from src.shared.websocket_manager import WebSocketManager

from .wheel import Wheel


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
