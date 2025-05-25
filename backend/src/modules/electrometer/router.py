from fastapi import APIRouter, BackgroundTasks
from src.shared.models import BaseResponse
from src.modules.electrometer.models import ElectrometerState
from src.modules.electrometer.module import ControllerDep

router = APIRouter(
    tags=["electrometer"],
    prefix="",
)


@router.post("/{device_id}/connect/{ip}", response_model=BaseResponse)
def connect_to_electrometer(ip: str, controller: ControllerDep, background_tasks: BackgroundTasks):
    """
    Connect to the electrometer with the given device ID.
    """
    resp = controller.connect_to_keysight_em(ip)

    background_tasks.add_task(controller.init_settings)

    return BaseResponse(
        message=f"Connected to {controller.device_id.value} at {ip}, IDN: {resp}"
    )

@router.get("/{device_id}/state", response_model=ElectrometerState)
async def get_electrometer_state(controller: ControllerDep):
    """
    Get the current state of the electrometer.
    """
    return controller.state.get()
