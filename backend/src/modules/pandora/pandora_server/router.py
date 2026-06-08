import logging
from fastapi import (
    APIRouter,
    HTTPException,
    status,
    WebSocket,
    WebSocketDisconnect,
)

from .models import BaseResponse
from .module import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["pandora-control-server"],
)

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
