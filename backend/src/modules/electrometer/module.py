from typing import Annotated
from fastapi import Depends
from src.core.state_manager import DeviceStateManager
from src.shared.persistent_session_manager import PersistentSessionManager
from src.modules.electrometer.db import engine, init_db
from src.modules.electrometer.controller import KeysightEM
from src.modules.electrometer.models import ElectrometerState, ElectrometerID

class ModuleState:
    controllers: dict[ElectrometerID, KeysightEM] = {}
    state_managers: dict[ElectrometerID, DeviceStateManager[ElectrometerState]] = {}
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

def init_module() -> None:
    """
    Initialize the module.
    """
    init_db()

    device_ids = [ElectrometerID.EM_1, ElectrometerID.EM_2]

    for device_id in device_ids:
        session_manager = PersistentSessionManager(engine)
        session_manager.init_session()

        module_state.session_managers[device_id] = session_manager

        session = session_manager.get_session()

        state_manager = DeviceStateManager(
            model=ElectrometerState,
            device_id=device_id,
            session=session,
        )
        
        controller = KeysightEM(device_id=device_id, state_manager=state_manager, db_session=session)
        module_state.state_managers[device_id] = state_manager
        module_state.controllers[device_id] = controller

def shutdown_module() -> None:
    """
    Shutdown the module.
    """
    for _, session_manager in module_state.session_managers.items():
        session_manager.close_session()
