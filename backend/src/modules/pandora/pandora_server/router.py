import logging
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from .models import BaseResponse, PandoraState
from .module import ws_manager, PandoraServerDep

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["pandora-control-server"],
)

@router.get("/state", response_model=PandoraState)
def get_state(pandora_server: PandoraServerDep):
    """
    Get the current state of the server.
    """
    pandora_server.wheels_controller.update_wheels_state()
    pandora_server.relays_controller.update_relays_state()
    pandora_server.state.update()  # publish to websocket manager
    return pandora_server.state.get()


@router.get("/health-check", response_model=BaseResponse)
def health_check():
    """
    Get the current status of the server.
    """
    return BaseResponse(
        message="PANDORA Control Server is running and accessible."
    )

@router.websocket("/ws")
async def chopper_wheel_ws(websocket: WebSocket):
    device_name = 'pandora-server'
    await ws_manager.connect(device_name, websocket)
    try:
        logger.info("WebSocket connection established for %s", device_name)
        while True:
            message = await websocket.receive_text()
            logger.info("Received websocket message from %s: %s", device_name, message)
    except WebSocketDisconnect:
        await ws_manager.disconnect(device_name, websocket)
