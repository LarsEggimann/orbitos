import logging

from typing import Annotated
from fastapi import Depends

from src.shared.state_manager import StateManager

from .pandora_wheels.controller import WheelsController

# imports from parent folders ... I think this is not very clean, but I can reuse the stuff I already have so I think it makes sense for now
from src.shared.websocket_manager import WebSocketManager
from src.modules.pandora.models import (
    PandoraState,
    PandoraDataResponse,
    PandoraSettings,
)

ws_manager = WebSocketManager[
    PandoraState, PandoraDataResponse, PandoraSettings
]()

logger = logging.getLogger(__name__)

class PandoraServer:
    wheels_controller: WheelsController

    def __init__(
            self,
            device_name: str,
            # ws_manager_: WebSocketManager[PandoraState, PandoraDataResponse, PandoraSettings]
            ):
        logger.info("Initializing pandora server instance")
        self.device_name = device_name
        # self.ws_manager = ws_manager_

        self.state: StateManager[PandoraState] = StateManager(
            model=PandoraState,
            device_name=self.device_name,
            on_state_update=ws_manager.broadcast_state_sync,
        )

pandora_server = PandoraServer(
    device_name='pandora-server',
    # ws_manager=ws_manager
    )

def init_pandora_server():
    logger.info("Initializing PANDORA Control Server modules ...")
    pandora_server.wheels_controller = WheelsController(
        state=pandora_server.state,
        ws_manager=ws_manager
    )

def shutdown_pandora_server():
    logger.info("Shutting down PANDORA Control Server modules ...")
    # TODO: actually add shutdown logic for all controllers

def get_pandora_server() -> PandoraServer:
    """
    Get the pandora server instance we use to store state and stuff
    """
    if pandora_server is None:
        raise ValueError("Pandora server instance not found")
    return pandora_server

PandoraServerDep = Annotated[PandoraServer, Depends(get_pandora_server)]
