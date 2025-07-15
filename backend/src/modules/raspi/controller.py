import logging
import time
import threading

import pyvisa
import numpy as np
from sqlmodel import Session
from pyvisa.resources import TCPIPSocket

from src.core.config import config
from src.shared.websocket_manager import WebSocketManager
from src.shared.settings_manager import SettingsManager
from src.shared.state_manager import StateManager
from src.modules.raspi.models import (
    RaspiState,
    RaspiDataResponse,
    RaspiSettings,
)
from src.shared.models import ConnectionStatus
from src.core.db import engine

logger = logging.getLogger()


class RaspiController:
    def __init__(
        self,
        device_id: int,
        device_name: str,
        ws_manager: WebSocketManager[
            RaspiState, RaspiDataResponse, RaspiSettings
        ],
    ):
        logger.info(
            "Initializing raspi controller"
        )

        self.device_id = device_id
        self.device_name = device_name
        self.ws_manager = ws_manager

        self.settings: SettingsManager[RaspiSettings] = SettingsManager(
            model=RaspiSettings,
            device_id=self.device_id,
            device_name=self.device_name,
            engine=engine,
            on_settings_update=self.ws_manager.broadcast_setting_sync,
        )

        self.state: StateManager[RaspiState] = StateManager(
            model=RaspiState,
            device_name=self.device_name,
            on_state_update=self.ws_manager.broadcast_state_sync,
        )

