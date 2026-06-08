import logging
from typing import Annotated, Generator
from fastapi import Depends
from src.shared.websocket_manager import WebSocketManager
from src.modules.pandora.models import (
    PandoraState,
    PandoraDataResponse,
    PandoraSettings,
)
from src.modules.pandora.controller import PandoraController
from src.modules.pandora.client.pandora_server_api_client import Client

logger = logging.getLogger(__name__)

class ModuleState:
    controller: PandoraController | None = None
    pandora_client: Client | None = None


module_state = ModuleState()


def get_controller() -> PandoraController:
    """
    Get the pandora controller.
    """
    if module_state.controller is None:
        raise ValueError("Controller for pandora not found")
    return module_state.controller

def init_client(host: str, port: int) -> Client:
    """
    Initialize the pandora server client.
    """
    module_state.pandora_client = Client(base_url=f'http://{host}:{port}')
    return module_state.pandora_client

def get_pandora_client() -> Client:
    """
    Get the pandora server client.
    """
    if module_state.pandora_client is None:
        if module_state.controller is None:
            raise ValueError("Controller for pandora not found")
        module_state.pandora_client = init_client(
            host=module_state.controller.settings.get().host,
            port=module_state.controller.settings.get().port,
        )
    return module_state.pandora_client

ControllerDep = Annotated[PandoraController, Depends(get_controller)]
PandoraClientDep = Annotated[Client, Depends(get_pandora_client)]

ws_manager = WebSocketManager[
    PandoraState, PandoraDataResponse, PandoraSettings
]()


def init_module() -> None:
    """
    Initialize the module.
    """
    logger.info("Initializing pandora module ...")

    # Initialize the controller with a device ID and name
    module_state.controller = PandoraController(
        device_id=1,
        device_name="pandoras-box",
        ws_manager=ws_manager,
    )


def shutdown_module() -> None:
    """
    Shutdown the module.
    """
    pass
