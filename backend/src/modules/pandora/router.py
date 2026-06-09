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
from src.modules.pandora.models import (
    PandoraDataResponse,
    PandoraSettings,
    PandoraState,
)

from src.modules.pandora.module import ControllerDep#, PandoraClientDep
from src.modules.pandora.module import ws_manager
from src.modules.pandora.db import SessionDep

def run_ssh(host: str, command: str):
    return subprocess.run(["ssh", host, command], capture_output=True, text=True, check=False)

def run_ssh_async(host: str, command: str):
    """Run SSH command without waiting for response"""
    return subprocess.Popen(["ssh", host, command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["pandora"],
    prefix="/pandora",
)

def raise_server_error(message: str):
    """Raise an HTTPException with a server error message."""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message
    )


@router.post("/server/start", response_model=BaseResponse)
async def start_server(controller: ControllerDep):
    """
    Try to start the server on the host.
    """
    host = controller.settings.get().host
    port = controller.settings.get().port
    pandora_server_directory = controller.settings.get().pandora_server_app_directory

    # Use 'bash -c' with proper backgrounding and input/output redirection to ensure SSH exits
    command = f"cd {pandora_server_directory} && nohup bash ./startup.sh </dev/null >out.log 2>&1 & disown"

    logger.info("Starting pandora server on %s:%d", host, port)
    
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
    
    # gracefully kill the server process by sending SIGINT first, then SIGKILL if it doesn't stop within a few seconds
    command = "pkill -2 -f 'fastapi run main.py' || true; sleep 10; pkill -9 -f 'fastapi run main.py' || true"
    
    logger.info("Stopping pandora server on %s", host)
    process = run_ssh_async(host, command)
    
    return BaseResponse(
        message=f"Server stop command executed on {host}. Process ID: {process.pid}"
    )

# @router.get("/server/health-check", response_model=BaseResponse)
# async def server_health_check(client: PandoraClientDep, controller: ControllerDep):
#     """
#     Check if the server is running on the host.
#     """
#     try:
#         response = await pandora_server_health_check.asyncio_detailed(client=client)
#         if response.status_code == status.HTTP_200_OK:
#             controller.state.update(connection_status=ConnectionStatus.CONNECTED)
#             return response.parsed
#         else:
#             raise_server_error(
#                 f"Unexpected status code {response.status_code} from server health check, content: {response.content.decode()}"
#             )
#     except Exception as e:
#         logger.error("Error connecting to pandora server: %s", e)
#         controller.state.update(connection_status=ConnectionStatus.DISCONNECTED)
#         raise_server_error("Failed to connect to pandora server.")
 
# async def update_bus_status(client: PandoraClientDep, controller: ControllerDep):
#     """
#     Update the bus status by fetching it from the pandora server.
#     """
#     try:
#         response = await pandora_server_get_status.asyncio_detailed(client=client)
#         if response.status_code == status.HTTP_200_OK:
#             if response.parsed is not None:
#                 to_dict = response.parsed.to_dict()
#                 # try to convert keys to int and values to BusStatus
#                 new_dict = {int(k): BusStatus(**v) for k, v in to_dict.items()}
#                 controller.state.update(bus_status=new_dict)
#                 return new_dict
#         else:
#             raise_server_error(
#                 f"Unexpected status code {response.status_code} from server status check, content: {response.content.decode()}"
#             )
#     except Exception as e:
#         logger.error("Error reading lin_act status: %s", e)
#         controller.state.update(bus_status=None)
#         raise_server_error("Failed to read lin_act status.")

# @router.get("/bus/status", response_model=dict[int, BusStatus])
# async def get_bus_status(client: PandoraClientDep, controller: ControllerDep):
#     """
#     Get the current status of the lin_acts.
#     """
#     return await update_bus_status(client, controller)

# @router.get("/state", response_model=PandoraState)
# async def get_state(client: PandoraClientDep, controller: ControllerDep):
#     """
#     Get the current state of the pandora module.
#     """
#     await update_bus_status(client, controller)
#     return controller.state.get()


@router.get("/settings", response_model=PandoraSettings)
async def get_settings(controller: ControllerDep):
    """
    Get the current settings for the pandora server.
    """
    return controller.settings.get()

@router.websocket("/ws")
async def pandora_ws(websocket: WebSocket, controller: ControllerDep):
    device_name = controller.device_name
    await ws_manager.connect(device_name, websocket)
    try:
        logger.info("WebSocket connection established for %s", device_name)
        while True:
            message = await websocket.receive_text()
            logger.info("Received websocket message from %s: %s", device_name, message)
    except WebSocketDisconnect:
        await ws_manager.disconnect(device_name, websocket)
