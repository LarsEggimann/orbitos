import logging
from fastapi import (
    APIRouter,
    BackgroundTasks,
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
def go_to_position(wheel_id: int, angle_deg: float, pandora_server: PandoraServerDep, background_tasks: BackgroundTasks):
    """
    Move the wheel with the given ID to the specified angle in degrees.
    """
    background_tasks.add_task(
        pandora_server.wheels_controller.go_to_position, wheel_id, angle_deg
    )

    return BaseResponse(
        message=f"Wheel {wheel_id} is moving to position {angle_deg} degrees."
    )

@router.post("/{wheel_id}/start-reference-search", response_model=BaseResponse)
def start_reference_search(wheel_id: int, pandora_server: PandoraServerDep, background_tasks: BackgroundTasks):
    """
    Start the reference search for the wheel with the given ID.
    """
    background_tasks.add_task(
        pandora_server.wheels_controller.start_reference_search, wheel_id
    )

    return BaseResponse(
        message=f"Wheel {wheel_id} is starting reference search."
    )

@router.post("/{wheel_id}/stop-reference-search", response_model=BaseResponse)
def stop_reference_search(wheel_id: int, pandora_server: PandoraServerDep, background_tasks: BackgroundTasks):
    """
    Stop the reference search for the wheel with the given ID.
    """
    background_tasks.add_task(
        pandora_server.wheels_controller.stop_reference_search, wheel_id
    )

    return BaseResponse(
        message=f"Wheel {wheel_id} is stopping reference search."
    )




