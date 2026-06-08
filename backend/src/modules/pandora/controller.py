import logging

from src.shared.websocket_manager import WebSocketManager
from src.shared.settings_manager import SettingsManager
from src.shared.state_manager import StateManager
from src.modules.pandora.models import (
    PandoraState,
    PandoraDataResponse,
    PandoraSettings,
)
from src.core.db import engine

logger = logging.getLogger()


class PandoraController:
    def __init__(
        self,
        device_id: int,
        device_name: str,
        ws_manager: WebSocketManager[
            PandoraState, PandoraDataResponse, PandoraSettings
        ],
    ):
        logger.info(
            "Initializing pandora controller"
        )

        self.device_id = device_id
        self.device_name = device_name
        self.ws_manager = ws_manager

        self.settings: SettingsManager[PandoraSettings] = SettingsManager(
            model=PandoraSettings,
            device_id=self.device_id,
            device_name=self.device_name,
            engine=engine,
            on_settings_update=self.ws_manager.broadcast_setting_sync,
        )

        self.state: StateManager[PandoraState] = StateManager(
            model=PandoraState,
            device_name=self.device_name,
            on_state_update=self.ws_manager.broadcast_state_sync,
        )

