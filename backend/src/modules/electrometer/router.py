import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlmodel import select, asc
from datetime import timezone
from src.shared.deps import TimeFrameInputDep
from src.shared.models import BaseResponse, ConnectionStatus
from src.modules.electrometer import module as electrometer_module
from src.modules.electrometer.models import (
    ElectrometerState,
    CurrentDataResponse,
    CurrentData,
    ElectrometerID,
)
from src.modules.electrometer.module import ControllerDep
from src.modules.electrometer.db import SessionDep
from src.modules.electrometer.module import ws_manager

logger = logging.getLogger(__name__)

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
            detail=f"{controller.device_id} is not connected. Please connect first.",
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

@router.post("/{device_id}/disconnect", response_model=BaseResponse)
def disconnect_electrometer(controller: ControllerDep):
    """
    Disconnect the electrometer.
    """
    assert_connected(controller)
    controller.disconnect_from_keysight_em()
    return BaseResponse(
        message=f"Disconnected from {controller.device_id.value}."
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


@router.get("/{device_id}/data")
async def get_current_data(
    device_id: ElectrometerID, session: SessionDep, time_frame: TimeFrameInputDep
):
    """
    Get the current data from the electrometer for a specified time frame.
    """
    statement = select(
        CurrentData.time, CurrentData.current, CurrentData.device_id
    ).where(CurrentData.device_id == device_id.value)

    log_string = f"Fetching data from {device_id.value}"

    if time_frame.start:
        log_string += f" from {time_frame.start}-{time_frame.start.tzinfo}"

        if time_frame.start.tzinfo is None:
            time_frame.start = time_frame.start.replace(tzinfo=timezone.utc)

        statement = statement.where(CurrentData.time >= time_frame.start.timestamp())
    if time_frame.end:
        log_string += f" to {time_frame.end}-{time_frame.end.tzinfo}"

        if time_frame.end.tzinfo is None:
            time_frame.end = time_frame.end.replace(tzinfo=timezone.utc)

        statement = statement.where(CurrentData.time <= time_frame.end.timestamp())

    logger.info(log_string)

    # sort by timestamp ascending
    statement = statement.order_by(asc(CurrentData.time))

    session_hr = session.exec(statement).all()

    time, current, device_ids = zip(*session_hr) if session_hr else ([], [], [])

    return CurrentDataResponse(
        device_id=device_ids[0] if device_ids else device_id.value,
        current=list(current),
        time=list(time),
    )


@router.post("/{device_id}/continuous-measurement/start", response_model=BaseResponse)
def start_continuous_measurement(controller: ControllerDep):
    """
    Start continuous measurement on the electrometer.
    """
    assert_connected(controller)
    controller.start_continuous_measurement()
    return BaseResponse(
        message=f"Continuous measurement started for {controller.device_id.value}"
    )


@router.post("/{device_id}/continuous-measurement/stop", response_model=BaseResponse)
def stop_continuous_measurement(controller: ControllerDep):
    """
    Stop continuous measurement on the electrometer.
    """
    controller.stop_continuous_measurement()
    return BaseResponse(
        message=f"Continuous measurement stopped for {controller.device_id.value}"
    )


@router.post(
    "/{device_id}/trigger-based-measurement/initialize", response_model=BaseResponse
)
def initialize_trigger_based_measurement(controller: ControllerDep):
    """
    Initialize trigger-based measurement on the electrometer.
    """
    assert_connected(controller)
    controller.init_trigger_based_measurement()
    return BaseResponse(
        message=f"Trigger-based measurement initialized for {controller.device_id.value}"
    )


@router.post(
    "/{device_id}/trigger-based-measurement/start", response_model=BaseResponse
)
def start_trigger_based_measurement(controller: ControllerDep, background_tasks: BackgroundTasks):
    """
    Start trigger-based measurement on the electrometer.
    """
    assert_connected(controller)
    if controller.trigger_based_measurement_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trigger-based measurement is already running for {controller.device_id.value}.",
        )
    
    background_tasks.add_task(controller.do_trigger_based_measurement)
    return BaseResponse(
        message=f"Trigger-based measurement started for {controller.device_id.value}"
    )


@router.websocket("/ws/electrometer/{device_id}")
async def electrometer_ws(websocket: WebSocket, device_id: str):
    await ws_manager.connect(device_id, websocket)
    try:
        while True:
            test = await websocket.receive_text()
            logger.info(f"Received message from {device_id}: {test}")
    except WebSocketDisconnect:
        await ws_manager.disconnect(device_id, websocket)
