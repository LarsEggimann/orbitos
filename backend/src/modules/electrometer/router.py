from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from src.shared.models import BaseResponse, ConnectionStatus
from src.modules.electrometer import module as electrometer_module
from src.modules.electrometer.models import ElectrometerState
from src.modules.electrometer.module import ControllerDep

router = APIRouter(
    tags=["electrometer"],
    prefix="",
)

def assert_connected(controller: ControllerDep):
    """
    Assert that the electrometer is connected.
    """
    if controller.state.get().connection_status != ConnectionStatus.CONNECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{controller.device_id} is not connected. Please connect first."
        )


@router.post("/{device_id}/connect/{ip}", response_model=BaseResponse)
def connect_to_electrometer(
    ip: str, controller: ControllerDep, background_tasks: BackgroundTasks
):
    """
    Connect to the electrometer with the given device ID.
    """
    resp = controller.connect_to_keysight_em(ip)
    background_tasks.add_task(controller.init_settings)
    return BaseResponse(
        message=f"Connected to {controller.device_id.value} at {ip}, IDN: {resp}"
    )


@router.post("/electrometers/reset", response_model=BaseResponse)
def reset_electrometer():
    """
    Reset the electrometer.
    """
    electrometer_module.shutdown_module()
    electrometer_module.init_module()
    return BaseResponse(message="All electrometers have been reset.")


@router.get("/{device_id}/state", response_model=ElectrometerState)
async def get_electrometer_state(controller: ControllerDep):
    """
    Get the current state of the electrometer.
    """
    return controller.state.get()


@router.post("/{device_id}/continuous-measurement/start", response_model=BaseResponse)
def start_continuous_measurement(controller: ControllerDep):
    """
    Start continuous measurement on the electrometer.
    """
    assert_connected(controller)
    controller.start_continuous_measurement()
    return BaseResponse(message=f"Continuous measurement started for {controller.device_id.value}")


@router.post("/{device_id}/continuous-measurement/stop", response_model=BaseResponse)
def stop_continuous_measurement(controller: ControllerDep):
    """
    Stop continuous measurement on the electrometer.
    """
    controller.stop_continuous_measurement()
    return BaseResponse(message=f"Continuous measurement stopped for {controller.device_id.value}")


@router.post("/{device_id}/trigger-based-measurement/initialize", response_model=BaseResponse)
def initialize_trigger_based_measurement(controller: ControllerDep):
    """
    Initialize trigger-based measurement on the electrometer.
    """
    assert_connected(controller)
    controller.init_trigger_based_measurement()
    return BaseResponse(message=f"Trigger-based measurement initialized for {controller.device_id.value}")


@router.post("/{device_id}/trigger-based-measurement/start", response_model=BaseResponse)
def start_trigger_based_measurement(controller: ControllerDep):
    """
    Start trigger-based measurement on the electrometer.
    """
    assert_connected(controller)
    controller.do_trigger_based_measurement()
    return BaseResponse(message=f"Trigger-based measurement started for {controller.device_id.value}")
