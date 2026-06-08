import logging
from fastapi import (
    APIRouter,
    HTTPException,
    status,
    WebSocket,
    WebSocketDisconnect,
)

from .models import BaseResponse
from .main import ws_manager

logger = logging.getLogger(__name__)

DEVICE_BUS = 1
DEVICE_ADDR = 0x10

# try import smbus (apt package on raspi)
try:
    import smbus # type: ignore
    # -> to install on raspi: sudo apt install -y i2c-tools python3-smbus
except ImportError:
    logger.warning("native smbus not available, using smbus3")
    import smbus3 as smbus  # use for local development

# Global bus instance - initialized lazily
_bus = None

def bus() -> smbus.SMBus:
    """Get or initialize the SMBus connection."""
    global _bus
    if _bus is None:
        _bus = smbus.SMBus(DEVICE_BUS)
    return _bus

router = APIRouter(
    tags=["pandora-server"],
    prefix="/pandora-server",
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

