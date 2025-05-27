from typing import Annotated
from fastapi import Depends
from src.shared.persistent_session_manager import PersistentSessionManager
from src.modules.electrometer.db import engine, init_db
from src.modules.electrometer.controller import KeysightEM
from src.modules.electrometer.models import ElectrometerID
from src.shared.websocket_manager import WebSocketManager
from src.modules.electrometer.models import ElectrometerState, CurrentDataResponse


class ModuleState:
    controllers: dict[ElectrometerID, KeysightEM] = {}
    session_managers: dict[ElectrometerID, PersistentSessionManager] = {}


module_state = ModuleState()


def get_controller(device_id: ElectrometerID) -> KeysightEM:
    """
    Get the controller for the given device ID.
    """
    if device_id not in module_state.controllers:
        raise ValueError(f"Controller for device {device_id} not found")
    return module_state.controllers[device_id]


ControllerDep = Annotated[KeysightEM, Depends(get_controller)]

ws_manager = WebSocketManager[ElectrometerState, CurrentDataResponse]()

def init_module() -> None:
    """
    Initialize the module.
    """
    init_db()

    device_ids = ElectrometerID.__members__.values()

    for device_id in device_ids:
        session_manager = PersistentSessionManager(engine)
        session_manager.init_session()

        module_state.session_managers[device_id] = session_manager

        session = session_manager.get_session()

        controller = KeysightEM(device_id=device_id, db_session=session, ws_manager=ws_manager)
        module_state.controllers[device_id] = controller


def shutdown_module() -> None:
    """
    Shutdown the module.
    """
    for _, session_manager in module_state.session_managers.items():
        session_manager.close_session()
