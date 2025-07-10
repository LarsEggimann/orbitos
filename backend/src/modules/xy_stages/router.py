import logging
from fastapi import (
    APIRouter,
    HTTPException,
    status,
    WebSocket,
    WebSocketDisconnect,
)
from sqlmodel import select, asc
from src.modules.xy_stages.arcus_performax_stage import ArcusPerformaxStage
from src.shared.deps import TimeFrameInputDep
from src.shared.models import BaseResponse, ConnectionStatus
from src.modules.xy_stages.module import ControllerDep
from src.modules.xy_stages.db import SessionDep
from src.modules.xy_stages.module import ws_manager
from src.modules.xy_stages.models import (
    XY,
    XYStagesStatus,
    XYStagesDataResponse,
    XYStagesData,
    PerformaxUSBDevice,
    XYStagesSettings,
    XYStagesSettingsSet,
    XYStagesState,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["xy-stages"],
    prefix="/xy-stages",
)


def assert_connected(controller: ControllerDep):
    """
    Assert that stage is connected.
    """
    if controller.state.get().connection_status != ConnectionStatus.CONNECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{controller.device_name} is not connected. Please connect first.",
        )

def assert_idle(controller: ControllerDep):
    """
    Assert that stage is idle.
    """
    if controller.state.get().status != XYStagesStatus.IDLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{controller.device_name} is not idle. Please wait.",
        )

def assert_no_errors(controller: ControllerDep):
    """
    Assert that the stage has no errors.
    """
    if controller.state.get().error is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{controller.device_name} has pending error, reset the error.",
        )

def assert_stage_idle(stage: ArcusPerformaxStage):
    """
    Assert that the stage is idle.
    """
    if stage.state.moving is True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{stage.name} is currently moving. Please wait until it is idle.",
        )

def assert_stage_connected(stage: ArcusPerformaxStage):
    """
    Assert that the stage is connected.
    """
    if stage.state.connection_status != ConnectionStatus.CONNECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{stage.name} is not connected. Please connect first.",
        )

@router.get("/usb-devices", response_model=list[PerformaxUSBDevice])
def get_available_usb_devices(controller: ControllerDep):
    """
    Get the available Performax USB Devices for the xy stages.
    """
    try:
        devices = controller.xy_stages[XY.X_AXIS].list_usb_performax_devices()
    except Exception as e:
        logger.error("Failed to get COM ports: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available COM ports.",
        ) from e
    return devices


@router.post("/connect/{axis}/{index}", response_model=BaseResponse)
def connect_to_stage(axis: XY, index: int, controller: ControllerDep):
    """
    Connect to the axis motor.
    """
    try:
        controller.connect(axis, index)
    except Exception as e:
        logger.error(
            "Failed to connect to %s at index %s: %s", controller.device_name, index, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect to {controller.device_name} at index {index}.",
        ) from e

    return BaseResponse(
        message=f"Connected to {controller.device_name} at index {index}."
    )



@router.post("/disconnect/{axis}", response_model=BaseResponse)
def disconnect_stage(axis: XY, controller: ControllerDep):
    """
    Disconnect stage at given axis.
    """
    assert_connected(controller)
    assert_idle(controller)
    controller.disconnect(axis)
    return BaseResponse(message=f"Disconnected from {controller.device_name} at {axis}.")


@router.get("/data", response_model=XYStagesDataResponse)
async def get_stages_data(session: SessionDep, time_frame: TimeFrameInputDep):
    """
    Get the position data of the xy stages for a specified time frame.
    """
    statement = select(XYStagesData.timestamp, XYStagesData.x_position, XYStagesData.y_position)

    log_string = "Fetching data from xy stages "

    if time_frame.start:
        log_string += f" from {time_frame.start}-{time_frame.start.tzinfo}"
        statement = statement.where(XYStagesData.timestamp >= time_frame.start.timestamp())
    if time_frame.end:
        log_string += f" to {time_frame.end}-{time_frame.end.tzinfo}"
        statement = statement.where(XYStagesData.timestamp <= time_frame.end.timestamp())

    logger.info(log_string)

    # sort by timestamp ascending
    statement = statement.order_by(asc(XYStagesData.timestamp))

    session_hr = session.exec(statement).all()

    time, x, y = zip(*session_hr) if session_hr else ([], [], [])

    return XYStagesDataResponse(
        device_name="xy_stages",
        timestamp=list(time),
        x_position=list(x),
        y_position=list(y),
    )


@router.get("/state", response_model=XYStagesState)
def get_stages_state(controller: ControllerDep):
    """
    Get the current state of the xy stages.
    """
    return controller.state.get()


@router.post("/state/reset-error", response_model=BaseResponse)
def reset_stages_error(controller: ControllerDep):
    """
    Reset the error state of the xy stages.
    """
    controller.state.update(error=None)
    return BaseResponse(message=f"Error state reset for {controller.device_name}.")


@router.get("/settings", response_model=XYStagesSettings)
def get_stages_settings(controller: ControllerDep):
    """
    Get the current settings of the xy stages.
    """
    return controller.settings.get()


@router.post("/settings", response_model=BaseResponse)
def set_stages_settings(settings: XYStagesSettingsSet, controller: ControllerDep):
    """
    Set the settings of the xy stages.
    """
    assert_connected(controller)
    assert_idle(controller)
    assert_no_errors(controller)

    controller.update_settings(settings)
    changed_fields = (
        controller.settings.get_changed_fields_compared_to_settings_before_change()
    )
    return BaseResponse(
        message=f"Settings updated for {controller.device_name}. Changed fields: {changed_fields}"
    )

@router.post('/{axis}/move-to/{position}', response_model=BaseResponse)
def move_axis_to_position(axis: XY, position: float, controller: ControllerDep):
    """
    Move the specified axis to a given position in mm.
    """
    assert_no_errors(controller)

    stage = controller.xy_stages[axis]

    assert_stage_idle(stage)
    assert_stage_connected(stage)

    try:
        controller.move_to(axis, position)
    except Exception as e:
        logger.error("Failed to move %s to position %s: %s", axis.value, position, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move {axis.value} to position {position} mm.",
        ) from e

    return BaseResponse(message=f"Moved {axis.value} to position {position} mm.")

@router.post('/{axis}/move-by/{position}', response_model=BaseResponse)
def move_axis_by_mm(axis: XY, mm: float, controller: ControllerDep):
    """
    Move the specified axis by a amount in mm.
    """
    assert_no_errors(controller)

    stage = controller.xy_stages[axis]

    assert_stage_idle(stage)
    assert_stage_connected(stage)

    try:
        controller.move_by(axis, mm)
    except Exception as e:
        logger.error("Failed to move %s to position %s: %s", axis.value, mm, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move {axis.value} to position {mm} mm.",
        ) from e

    return BaseResponse(message=f"Moved {axis.value} to position {mm} mm.")

@router.websocket("/ws")
async def xy_stages_ws(websocket: WebSocket, controller: ControllerDep):
    device_name = controller.device_name
    await ws_manager.connect(device_name, websocket)
    try:
        logger.info("WebSocket connection established for %s", device_name)
        while True:
            message = await websocket.receive_text()
            logger.info("Received websocket message from %s: %s", device_name, message)
    except WebSocketDisconnect:
        await ws_manager.disconnect(device_name, websocket)
