import logging
import subprocess

import httpx
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

def run_ssh_async(host: str, command: str):
    """Run SSH command without waiting for response"""
    return subprocess.Popen(["ssh", host, command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


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

    # Use 'bash -c' with proper backgrounding and input/output redirection to ensure SSH exits
    command = f"cd {raspi_server_directory} && nohup bash ./startup.sh </dev/null >out.log 2>&1 & disown"

    logger.info("Starting raspi server on %s:%d", host, port)
    
    # Start the process without waiting for it to complete
    process = run_ssh_async(host, command)
    
    return BaseResponse(
        message=f"Server startup command sent to {host}:{port} (PID: {process.pid})"
    )

@router.post("/server/stop", response_model=BaseResponse)
async def stop_server(controller: ControllerDep):
    """
    Stop the server on the host.
    """
    host = controller.settings.get().host
    
    # Kill any running FastAPI processes
    command = "pkill -f 'fastapi run main.py' || true"  # || true ensures command succeeds even if no process found
    
    logger.info("Stopping raspi server on %s", host)
    process = run_ssh_async(host, command)
    
    return BaseResponse(
        message=f"Server stop command executed on {host}. Process ID: {process.pid}"
    )

@router.get("/server/status", response_model=BaseResponse)
async def get_server_status(controller: ControllerDep):
    """
    Check if the server is running on the host.
    """
    request = httpx.get(
        f"http://{controller.settings.get().host}:{controller.settings.get().port}/raspi-server/status",
    )
    return BaseResponse(
        message=f"Server status check on {controller.settings.get().host}:{controller.settings.get().port} returned: {request.content.decode()}"
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
