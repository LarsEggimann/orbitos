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
from src.modules.chopperwheel.module import ControllerDep
from src.modules.chopperwheel.db import SessionDep
from src.modules.chopperwheel.module import ws_manager
from src.modules.chopperwheel.models import CWStatus, CWDataResponse, CWData

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["chopperwheel"],
    prefix="/chopperwheel",
)


def assert_connected(controller: ControllerDep):
    """
    Assert that the chopper wheel is connected.
    """
    if controller.state.get().connection_status != ConnectionStatus.CONNECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{controller.device_name} is not connected. Please connect first.",
        )


def assert_idle(controller: ControllerDep):
    """
    Assert that the chopper wheel is idle.
    """
    if controller.state.get().status != CWStatus.IDLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{controller.device_name} is not idle. Please wait.",
        )


def assert_no_errors(controller: ControllerDep):
    """
    Assert that the chopper wheel has no errors.
    """
    if controller.state.get().error is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{controller.device_name} has pending error, reset the error.",
        )


@router.post("/connect/{com_port}", response_model=BaseResponse)
def connect_to_chopper_wheel(com_port: str, controller: ControllerDep):
    """
    Connect to the chopper wheel.
    """
    if controller.state.get().connection_status == ConnectionStatus.CONNECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{controller.device_name} is already connected.",
        )

    controller.connect(com_port)
    ds = controller.init_motor_settings()
    return BaseResponse(
        message=f"Connected to {controller.device_name} at {com_port}, Drive Settings: {ds}"
    )


@router.post("/rotate-demo", response_model=BaseResponse)
def rotate_demo_chopper_wheel(
    controller: ControllerDep, background_tasks: BackgroundTasks
):
    """
    Rotate the chopper wheel in a demo mode.
    """
    assert_connected(controller)
    assert_idle(controller)
    background_tasks.add_task(controller.rotate_demo)
    return BaseResponse(
        message=f"Chopper wheel {controller.device_name} is rotating in demo mode."
    )


@router.post("/disconnect", response_model=BaseResponse)
def disconnect_chopper_wheel(controller: ControllerDep):
    """
    Disconnect the chopper wheel.
    """
    assert_connected(controller)
    assert_idle(controller)
    controller.disconnect()
    return BaseResponse(message=f"Disconnected from {controller.device_name}.")


@router.get("/data", response_model=CWDataResponse)
async def get_chopper_wheel_data(session: SessionDep, time_frame: TimeFrameInputDep):
    """
    Get the velocity and position data from the chopper wheel for a specified time frame.
    """
    statement = select(CWData.timestamp, CWData.velocity, CWData.angular_position)

    log_string = "Fetching data from chopper wheel "

    if time_frame.start:
        log_string += f" from {time_frame.start}-{time_frame.start.tzinfo}"
        statement = statement.where(CWData.timestamp >= time_frame.start.timestamp())
    if time_frame.end:
        log_string += f" to {time_frame.end}-{time_frame.end.tzinfo}"
        statement = statement.where(CWData.timestamp <= time_frame.end.timestamp())

    logger.info(log_string)

    # sort by timestamp ascending
    statement = statement.order_by(asc(CWData.timestamp))

    session_hr = session.exec(statement).all()

    time, velocity, angular_position, _ = (
        zip(*session_hr) if session_hr else ([], [], [])
    )

    return CWDataResponse(
        device_name="chopper_wheel",
        timestamp=list(time),
        velocity=list(velocity),
        angular_position=list(angular_position),
    )


@router.websocket("/ws")
async def chopper_wheel_ws(websocket: WebSocket, controller: ControllerDep):
    device_name = controller.device_name
    await ws_manager.connect(device_name, websocket)
    try:
        logger.info("WebSocket connection established for %s", device_name)
        while True:
            message = await websocket.receive_text()
            logger.info("Received websocket message from %s: %s", device_name, message)
    except WebSocketDisconnect:
        await ws_manager.disconnect(device_name, websocket)
