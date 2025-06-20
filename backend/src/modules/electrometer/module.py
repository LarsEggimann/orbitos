import logging
from typing import Annotated
from fastapi import Depends
from src.modules.electrometer.db import init_db
from src.modules.electrometer.controller import KeysightEM
from src.modules.electrometer.models import ElectrometerName
from src.shared.websocket_manager import WebSocketManager
from src.modules.electrometer.models import (
    ElectrometerSettings,
    ElectrometerDataResponse,
    ElectrometerState,
)

logger = logging.getLogger(__name__)


class ModuleState:
    controllers: dict[int, KeysightEM] = {}


module_state = ModuleState()


def get_controller(device_id: int) -> KeysightEM:
    """
    Get the controller for the given device ID.
    """
    if device_id not in module_state.controllers:
        raise ValueError(f"Controller for electrometer {device_id} not found")
    return module_state.controllers[device_id]


ControllerDep = Annotated[KeysightEM, Depends(get_controller)]

ws_manager = WebSocketManager[
    ElectrometerState, ElectrometerDataResponse, ElectrometerSettings
]()


def init_module() -> None:
    """
    Initialize the module.
    """
    logger.info("Initializing electrometer module ...")

    init_db()

    device_names = ElectrometerName.__members__.values()
    count_device_id = 1

    for device_name in device_names:
        controller = KeysightEM(
            device_id=count_device_id, device_name=device_name, ws_manager=ws_manager
        )
        module_state.controllers[count_device_id] = controller
        count_device_id += 1


def shutdown_module() -> None:
    """
    Shutdown the module.
    """
    logger.info("Shutting down electrometer module ...")
