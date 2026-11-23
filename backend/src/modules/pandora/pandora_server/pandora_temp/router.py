import logging
from fastapi import (
    APIRouter,
)

from ..models import BaseResponse
from ..module import PandoraServerDep

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["pandora-temperature-readout"],
    prefix="/temperature",
)

@router.post("/fetch", response_model=BaseResponse)
def fetch_temperature(pandora_server: PandoraServerDep):
    """
    Fetch the temperature from the arduino and update the state.
    """
    t_ambient, t_object = pandora_server.temperature_readout_controller.fetch_temperature()

    print(f"Fetched temperature: ambient={t_ambient:.2f} °C, object={t_object:.2f} °C")

    return BaseResponse(
        message="Temperature fetched successfully."
    )

