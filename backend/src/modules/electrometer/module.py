from typing import Annotated
from fastapi import Depends
from src.shared.persistent_session_manager import PersistentSessionManager
from src.modules.electrometer.db import engine, init_db
from src.modules.electrometer.router import router as electrometer_router
from src.modules.electrometer.controller import KeysightEM

router = electrometer_router
session_manager = PersistentSessionManager(engine)

class ModuleState:
    controller: KeysightEM | None = None

state = ModuleState()

ControllerDep = Annotated[KeysightEM, Depends(lambda: state.controller)]


def init_module() -> None:
    """
    Initialize the module.
    """
    init_db()
    session_manager.init_session()

    state.controller = KeysightEM(db_session=session_manager.get_session())

def shutdown_module() -> None:
    """
    Shutdown the module.
    """
    session_manager.close_session()
