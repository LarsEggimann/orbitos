import logging
from typing import Annotated, Generator
from fastapi import Depends
from src.shared.websocket_manager import WebSocketManager
from src.modules.raspi.models import (
    RaspiState,
    RaspiDataResponse,
    RaspiSettings,
)
from src.modules.raspi.controller import RaspiController
from src.modules.raspi.client.raspi_server_api_client import Client

logger = logging.getLogger(__name__)

class ModuleState:
    controller: RaspiController | None = None
    raspi_client: Client | None = None


module_state = ModuleState()


def get_controller() -> RaspiController:
    """
    Get the raspi controller.
    """
    if module_state.controller is None:
        raise ValueError("Controller for raspi not found")
    return module_state.controller

def init_client(host: str, port: int) -> Client:
    """
    Initialize the raspi server client.
    """
    module_state.raspi_client = Client(base_url=f'http://{host}:{port}')
    return module_state.raspi_client

def get_raspi_client() -> Client:
    """
    Get the raspi server client.
    """
    if module_state.raspi_client is None:
        if module_state.controller is None:
            raise ValueError("Controller for raspi not found")
        module_state.raspi_client = init_client(
            host=module_state.controller.settings.get().host,
            port=module_state.controller.settings.get().port,
        )
    return module_state.raspi_client

ControllerDep = Annotated[RaspiController, Depends(get_controller)]
RaspiClientDep = Annotated[Client, Depends(get_raspi_client)]

ws_manager = WebSocketManager[
    RaspiState, RaspiDataResponse, RaspiSettings
]()


def init_module() -> None:
    """
    Initialize the module.
    """
    logger.info("Initializing raspi module ...")

    # Initialize the controller with a device ID and name
    module_state.controller = RaspiController(
        device_id=1,
        device_name="raspi",
        ws_manager=ws_manager,
    )


def shutdown_module() -> None:
    """
    Shutdown the module.
    """
    pass
