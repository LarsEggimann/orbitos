import logging
from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    status,
    WebSocket,
    WebSocketDisconnect,
)
from sqlmodel import select, asc
from src.shared.deps import TimeFrameInputDep
from src.shared.models import BaseResponse, ConnectionStatus
from src.modules.electrometer import module as electrometer_module
from src.modules.electrometer.models import (
    ElectrometerSettings,
    ElectrometerDataResponse,
    ElectrometerData,
    ElectrometerName,
    ElectrometerSettingsSet,
    ElectrometerStatus,
    ElectrometerState,
)
from src.modules.electrometer.module import ControllerDep
from src.modules.electrometer.db import SessionDep
from src.modules.electrometer.module import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["electrometer"],
    prefix="/electrometer",
)


def assert_connected(controller: ControllerDep):
    """
    Assert that the electrometer is connected.
    """
    if controller.state.get().connection_status != ConnectionStatus.CONNECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{controller.device_name.value} is not connected. Please connect first.",
        )


def assert_idle(controller: ControllerDep):
    """
    Assert that the electrometer is idle.
    """
    if controller.state.get().status != ElectrometerStatus.IDLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{controller.device_name.value} is not idle. Please stop any ongoing measurements first.",
        )


def assert_no_errors(controller: ControllerDep):
    """
    Assert that the electrometer has no errors.
    """
    if controller.state.get().error is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{controller.device_name.value} has pending error, reset the error.",
        )


@router.post("/{device_id}/connect/{ip}", response_model=BaseResponse)
def connect_to_electrometer(
    ip: str, controller: ControllerDep, background_tasks: BackgroundTasks
):
    """
    Connect to the electrometer with the given device ID.
    """
    if controller.state.get().connection_status == ConnectionStatus.CONNECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{controller.device_name.value} is already connected.",
        )

    resp = controller.connect_to_keysight_em(ip)
    background_tasks.add_task(controller.init_settings)
    return BaseResponse(
        message=f"Connected to {controller.device_name.value} at {ip}, IDN: {resp}"
    )


@router.post("/{device_id}/disconnect", response_model=BaseResponse)
def disconnect_electrometer(controller: ControllerDep):
    """
    Disconnect the electrometer.
    """
    assert_connected(controller)
    controller.disconnect_from_keysight_em()
    return BaseResponse(message=f"Disconnected from {controller.device_name}.")


@router.post("/electrometers/reset", response_model=BaseResponse)
def reset_electrometer():
    """
    Reset all electrometers.
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


@router.get("/{device_id}/settings", response_model=ElectrometerSettings)
async def get_electrometer_settings(controller: ControllerDep):
    """
    Get the current settings of the electrometer.
    """
    return controller.settings.get()


@router.post("/{device_id}/settings", response_model=BaseResponse)
def set_electrometer_settings(
    controller: ControllerDep, settings: ElectrometerSettingsSet
):
    """
    Set the one or more setting of the electrometer.
    """
    assert_connected(controller)
    assert_idle(controller)
    assert_no_errors(controller)
    controller.update_settings(settings)
    changed_fields = controller.settings.get_changed_fields_compared_to_settings_before_change()
    return BaseResponse(
        message=f"Settings updated for {controller.device_name}. Changed fields: {changed_fields}"
    )


@router.post("/{device_id}/state/reset-error", response_model=BaseResponse)
def reset_electrometer_error(controller: ControllerDep):
    """
    Reset the error state of the electrometer.
    """
    controller.state.update(error=None)
    return BaseResponse(message=f"Error state reset for {controller.device_name}.")


@router.get("/{device_id}/data", response_model=ElectrometerDataResponse)
async def get_current_data(
    device_id: int, session: SessionDep, time_frame: TimeFrameInputDep
):
    """
    Get the current data from the electrometer for a specified time frame.
    """
    statement = select(
        ElectrometerData.timestamp, ElectrometerData.current, ElectrometerData.device_id
    ).where(ElectrometerData.device_id == device_id)

    log_string = f"Fetching data from electrometer {device_id}"

    if time_frame.start:
        log_string += f" from {time_frame.start}-{time_frame.start.tzinfo}"
        statement = statement.where(ElectrometerData.timestamp >= time_frame.start.timestamp())
    if time_frame.end:
        log_string += f" to {time_frame.end}-{time_frame.end.tzinfo}"
        statement = statement.where(ElectrometerData.timestamp <= time_frame.end.timestamp())

    logger.info(log_string)

    # sort by timestamp ascending
    statement = statement.order_by(asc(ElectrometerData.timestamp))

    session_hr = session.exec(statement).all()

    time, current, _ = zip(*session_hr) if session_hr else ([], [], [])    

    return ElectrometerDataResponse(
        device_name=ElectrometerName("electrometer_" + str(device_id)),
        current=list(current),
        timestamp=list(time),
    )


@router.post("/{device_id}/continuous-measurement/start", response_model=BaseResponse)
def start_continuous_measurement(controller: ControllerDep):
    """
    Start continuous measurement on the electrometer.
    """
    assert_connected(controller)
    assert_idle(controller)
    assert_no_errors(controller)
    controller.start_continuous_measurement()
    return BaseResponse(
        message=f"Continuous measurement started for {controller.device_name}"
    )


@router.post("/{device_id}/continuous-measurement/stop", response_model=BaseResponse)
def stop_continuous_measurement(controller: ControllerDep):
    """
    Stop continuous measurement on the electrometer.
    """
    controller.stop_continuous_measurement()
    return BaseResponse(
        message=f"Continuous measurement stopped for {controller.device_name}"
    )

@router.post(
    "/{device_id}/trigger-based-measurement/start", response_model=BaseResponse
)
def start_trigger_based_measurement(
    controller: ControllerDep, background_tasks: BackgroundTasks
):
    """
    Start trigger-based measurement on the electrometer.
    """
    assert_connected(controller)
    assert_idle(controller)
    assert_no_errors(controller)
    if controller.trigger_based_measurement_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trigger-based measurement is already running for {controller.device_name}.",
        )

    background_tasks.add_task(controller.do_trigger_based_measurement)
    return BaseResponse(
        message=f"Trigger-based measurement started for {controller.device_name}"
    )


@router.websocket("/ws/{device_id}")
async def electrometer_ws(websocket: WebSocket, controller: ControllerDep):
    device_name = controller.device_name.value
    await ws_manager.connect(device_name, websocket)
    try:
        logger.info("WebSocket connection established for %s", device_name)
        while True:
            message = await websocket.receive_text()
            logger.info("Received websocket message from %s: %s", device_name, message)
    except WebSocketDisconnect:
        await ws_manager.disconnect(device_name, websocket)
