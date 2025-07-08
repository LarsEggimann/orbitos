import logging
from typing import Annotated
from fastapi import Depends

from src.shared.websocket_manager import WebSocketManager
from src.modules.chopperwheel.controller import CWController
from src.modules.chopperwheel.models import (
    CWSettings,
    CWDataResponse,
    CWState,
)

logger = logging.getLogger(__name__)


class ModuleState:
    controller: CWController | None = None


module_state = ModuleState()


def get_controller() -> CWController:
    """
    Get the chopper wheel controller.
    """
    if module_state.controller is None:
        raise ValueError("Controller for chopper wheel not found")
    return module_state.controller


ControllerDep = Annotated[CWController, Depends(get_controller)]

ws_manager = WebSocketManager[CWState, CWDataResponse, CWSettings]()


def init_module() -> None:
    """
    Initialize the module.
    """
    logger.info("Initializing chopper wheel module ...")

    # init_db()

    module_state.controller = CWController(
        device_name="chopper_wheel", ws_manager=ws_manager
    )


def shutdown_module() -> None:
    """
    Shutdown the module.
    """
    logger.info("Shutting down chopper wheel module ...")
    if module_state.controller:
        module_state.controller.shutdown()
