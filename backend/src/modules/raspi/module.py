import logging
from typing import Annotated
from fastapi import Depends
from src.shared.websocket_manager import WebSocketManager
from src.modules.raspi.models import (
    RaspiState,
    RaspiDataResponse,
    RaspiSettings,
)
from src.modules.raspi.controller import RaspiController

logger = logging.getLogger(__name__)

class ModuleState:
    controller: RaspiController | None = None


module_state = ModuleState()


def get_controller() -> RaspiController:
    """
    Get the raspi controller.
    """
    if module_state.controller is None:
        raise ValueError("Controller for raspi not found")
    return module_state.controller


ControllerDep = Annotated[RaspiController, Depends(get_controller)]

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
