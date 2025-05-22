from typing import Annotated
from fastapi import Depends
from src.core.state_manager import DeviceStateManager
from src.shared.persistent_session_manager import PersistentSessionManager
from src.modules.electrometer.db import engine, init_db
from src.modules.electrometer.controller import KeysightEM
from src.modules.electrometer.models import ElectrometerState


session_manager = PersistentSessionManager(engine)

class ModuleState:
    device_controller: KeysightEM | None = None
    device_state_manager: DeviceStateManager[ElectrometerState] | None = None

module_state = ModuleState()

ControllerDep = Annotated[KeysightEM, Depends(lambda: module_state.device_controller)]


def init_module() -> None:
    """
    Initialize the module.
    """
    init_db()
    session_manager.init_session()

    module_state.device_state_manager = DeviceStateManager(
        model=ElectrometerState,
        device_id="1",
        session=session_manager.get_session(),
    )

    module_state.device_controller = KeysightEM(state_manager=module_state.device_state_manager, db_session=session_manager.get_session())

def shutdown_module() -> None:
    """
    Shutdown the module.
    """
    session_manager.close_session()
