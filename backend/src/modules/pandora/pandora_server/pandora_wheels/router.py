import logging
from fastapi import (
    APIRouter,
    HTTPException,
    status,
    WebSocket,
    WebSocketDisconnect,
)

from ..models import BaseResponse
from ..module import PandoraServerDep

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["pandora-wheels"],
    prefix="/wheels",
)

@router.post("/{wheel_id}/go-to-position/{angle_deg}", response_model=BaseResponse)
def go_to_position(wheel_id: int, angle_deg: float, pandora_server: PandoraServerDep):
    """
    Move the wheel with the given ID to the specified angle in degrees.
    """
    pandora_server.wheels_controller.go_to_position(wheel_id, angle_deg)

    return BaseResponse(
        message=f"Wheel {wheel_id} is moving to position {angle_deg} degrees."
    )




