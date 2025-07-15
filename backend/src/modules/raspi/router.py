import logging
import subprocess
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
from src.modules.raspi.models import (
    RaspiDataResponse,
    RaspiSettings,
    RaspiSettingsSet,
    RaspiState,
)
from src.core.db import SessionDep
from src.modules.raspi.module import ControllerDep
from src.modules.raspi.module import ws_manager

def run_ssh(host: str, command: str):
    return subprocess.run(["ssh", host, command], capture_output=True, text=True, check=False)

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["raspi"],
    prefix="/raspi",
)


@router.post("/server/start", response_model=BaseResponse)
async def install_server(controller: ControllerDep):
    """
    Try to start the server on the host.
    """
    host = controller.settings.get().host
    port = controller.settings.get().port
    raspi_server_directory = controller.settings.get().raspi_server_app_directory
    
    command = f"cd {raspi_server_directory} && nohup bash ./startup.sh > out.log 2>&1 &"

    logger.info("Starting raspi server on %s:%d", host, port)
    result = run_ssh(host, command)
    return BaseResponse(
        message=result.stdout
    )

    


@router.websocket("/ws")
async def raspi_ws(websocket: WebSocket, controller: ControllerDep):
    device_name = controller.device_name
    await ws_manager.connect(device_name, websocket)
    try:
        logger.info("WebSocket connection established for %s", device_name)
        while True:
            message = await websocket.receive_text()
            logger.info("Received websocket message from %s: %s", device_name, message)
    except WebSocketDisconnect:
        await ws_manager.disconnect(device_name, websocket)
