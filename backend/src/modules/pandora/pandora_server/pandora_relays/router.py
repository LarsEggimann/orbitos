import logging
from fastapi import (
    APIRouter,
)

from ..models import BaseResponse
from ..module import PandoraServerDep

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["pandora-relays"],
    prefix="/relays",
)

@router.post("/{relay_id}/on", response_model=BaseResponse)
def turn_on(relay_id: int, pandora_server: PandoraServerDep):
    """
    Turn on the relay with the given ID.
    """
    pandora_server.relays_controller.turn_on_relay(relay_id)
    return BaseResponse(
        message=f"Relay {relay_id} is now on."
    )

@router.post("/{relay_id}/off", response_model=BaseResponse)
def turn_off(relay_id: int, pandora_server: PandoraServerDep):
    """
    Turn off the relay with the given ID.
    """
    pandora_server.relays_controller.turn_off_relay(relay_id)
    return BaseResponse(
        message=f"Relay {relay_id} is now off."
    )
