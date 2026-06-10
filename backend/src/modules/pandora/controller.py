import logging

from src.shared.websocket_manager import WebSocketManager
from src.shared.settings_manager import SettingsManager
from src.shared.state_manager import StateManager
from src.modules.pandora.models import (
    PandoraState,
    PandoraDataResponse,
    PandoraSettings,
    PandoraSettingsSet,
)
from src.modules.pandora.pandora_server.models import PandoraState as PandoraServerState
from src.modules.pandora.db import engine

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

    def update_state(self, pandora_server_state: PandoraServerState) -> None:
        """
        Update the state of the pandora controller based on the state of the pandora server.
        """
        # get the fields that were actually set on the incoming server state
        set_fields = pandora_server_state.model_fields_set
        
        updates = {}
        for field in set_fields:
            # pull the attribute directly from the object (preserves sub-models)
            if hasattr(pandora_server_state, field):
                updates[field] = getattr(pandora_server_state, field)
        self.state.update(**updates)

    def update_settings(self, set_settings: PandoraSettingsSet) -> PandoraSettings:
        """
        Update the settings of the pandora controller.
        """

        self.settings.update(**set_settings.model_dump(exclude_unset=True))
        current_settings = self.settings.get()

        if self.state.get().error is not None:
            self.settings.undo_last_update()
            raise ValueError(
                f"Error while updating settings for pandora control {self.device_name}: {self.state.get().error}"
            )
        # return the changed settings
        logger.info(
            "Settings updated for pandora control %s: %s",
            self.device_name,
            current_settings.model_dump(exclude_unset=True),
        )
        return self.settings.get()

