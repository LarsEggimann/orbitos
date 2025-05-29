import logging
from typing import Annotated
from fastapi import Depends
from src.modules.electrometer.db import init_db
from src.modules.electrometer.controller import KeysightEM
from src.modules.electrometer.models import ElectrometerID
from src.shared.websocket_manager import WebSocketManager
from src.modules.electrometer.models import ElectrometerSettings, CurrentDataResponse, ElectrometerState

logger = logging.getLogger(__name__)

class ModuleState:
    controllers: dict[ElectrometerID, KeysightEM] = {}


module_state = ModuleState()


def get_controller(device_id: ElectrometerID) -> KeysightEM:
    """
    Get the controller for the given device ID.
    """
    if device_id not in module_state.controllers:
        raise ValueError(f"Controller for device {device_id} not found")
    return module_state.controllers[device_id]


ControllerDep = Annotated[KeysightEM, Depends(get_controller)]

ws_manager = WebSocketManager[ElectrometerState, CurrentDataResponse, ElectrometerSettings]()


def init_module() -> None:
    """
    Initialize the module.
    """
    logger.info("Initializing electrometer module ...")

    init_db()

    device_ids = ElectrometerID.__members__.values()

    for device_id in device_ids:
        controller = KeysightEM(
            device_id=device_id, ws_manager=ws_manager
        )
        module_state.controllers[device_id] = controller


def shutdown_module() -> None:
    """
    Shutdown the module.
    """
    logger.info("Shutting down electrometer module ...")
