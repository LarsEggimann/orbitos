import logging
from typing import Annotated
from fastapi import Depends

from src.shared.websocket_manager import WebSocketManager
from src.modules.xy_stages.controller import XYStagesController
from src.modules.xy_stages.models import (
    XYStagesSettings,
    XYStagesDataResponse,
    XYStagesState,
)

logger = logging.getLogger(__name__)


class ModuleState:
    controller: XYStagesController | None = None


module_state = ModuleState()


def get_controller() -> XYStagesController:
    """
    Get the xy stages controller.
    """
    if module_state.controller is None:
        raise ValueError("Controller for xy stages not found")
    return module_state.controller


ControllerDep = Annotated[XYStagesController, Depends(get_controller)]

ws_manager = WebSocketManager[XYStagesState, XYStagesDataResponse, XYStagesSettings]()


def init_module() -> None:
    """
    Initialize the module.
    """
    logger.info("Initializing xy stages module ...")

    # init_db()

    module_state.controller = XYStagesController(
        device_name="xy_stages", ws_manager=ws_manager
    )


def shutdown_module() -> None:
    """
    Shutdown the module.
    """
    logger.info("Shutting down xy stages module ...")
    if module_state.controller:
        module_state.controller.shutdown()
