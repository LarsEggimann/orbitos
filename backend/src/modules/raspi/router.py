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
from src.modules.raspi.client.raspi_server_api_client.api.raspi_server import raspi_server_get_status, raspi_server_health_check, raspi_server_extract_lin_act, raspi_server_retract_lin_act
from src.modules.raspi.module import ControllerDep, RaspiClientDep
from src.modules.raspi.module import ws_manager
from src.modules.raspi.raspi_server.models import BusStatus

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

def raise_server_error(message: str):
    """Raise an HTTPException with a server error message."""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message
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

@router.get("/server/health-check", response_model=BaseResponse)
async def server_health_check(client: RaspiClientDep, controller: ControllerDep):
    """
    Check if the server is running on the host.
    """
    try:
        response = await raspi_server_health_check.asyncio_detailed(client=client)
        if response.status_code == status.HTTP_200_OK:
            controller.state.update(connection_status=ConnectionStatus.CONNECTED)
            return response.parsed
        else:
            raise_server_error(
                f"Unexpected status code {response.status_code} from server health check, content: {response.content.decode()}"
            )
    except Exception as e:
        logger.error("Error connecting to raspi server: %s", e)
        controller.state.update(connection_status=ConnectionStatus.DISCONNECTED)
        raise_server_error("Failed to connect to raspi server.")
 
async def update_bus_status(client: RaspiClientDep, controller: ControllerDep):
    """
    Update the bus status by fetching it from the raspi server.
    """
    try:
        response = await raspi_server_get_status.asyncio_detailed(client=client)
        if response.status_code == status.HTTP_200_OK:
            if response.parsed is not None:
                to_dict = response.parsed.to_dict()
                controller.state.update(bus_status=to_dict)
                return to_dict
        else:
            raise_server_error(
                f"Unexpected status code {response.status_code} from server status check, content: {response.content.decode()}"
            )
    except Exception as e:
        logger.error("Error reading lin_act status: %s", e)
        controller.state.update(bus_status=None)
        raise_server_error("Failed to read lin_act status.")

@router.get("/bus/status", response_model=dict[int, BusStatus])
async def get_bus_status(client: RaspiClientDep, controller: ControllerDep):
    """
    Get the current status of the lin_acts.
    """
    return await update_bus_status(client, controller)
    
@router.post("/lin-act/{lin_act_id}/extract", response_model=BaseResponse)
async def extract_lin_act(lin_act_id: int, client: RaspiClientDep, controller: ControllerDep):
    """
    Switch lin act assigned to the given ID to the 'extract' position.
    """
    try:
        response = await raspi_server_extract_lin_act.asyncio_detailed(
            lin_act_id=lin_act_id, client=client
        )
        if response.status_code == status.HTTP_200_OK:
            await update_bus_status(client, controller)
            return BaseResponse(
                message=f"lin_act {lin_act_id} switched to extract position."
            )
        else:
            raise_server_error(
                f"Unexpected status code {response.status_code} from extract command, content: {response.content.decode()}"
            )
    except Exception as e:
        logger.error("Error extracting lin_act %d: %s", lin_act_id, e)
        raise_server_error(f"Failed to extract lin_act {lin_act_id}.")

@router.post("/lin-act/{lin_act_id}/retract", response_model=BaseResponse)
async def retract_lin_act(lin_act_id: int, client: RaspiClientDep, controller: ControllerDep):
    """
    Switch lin act assigned to the given ID to the 'retract' position.
    """
    try:
        response = await raspi_server_retract_lin_act.asyncio_detailed(
            lin_act_id=lin_act_id, client=client
        )
        if response.status_code == status.HTTP_200_OK:
            await update_bus_status(client, controller)
            return BaseResponse(
                message=f"lin_act {lin_act_id} switched to retract position."
            )
        else:
            raise_server_error(
                f"Unexpected status code {response.status_code} from retract command, content: {response.content.decode()}"
            )
    except Exception as e:
        logger.error("Error retracting lin_act %d: %s", lin_act_id, e)
        raise_server_error(f"Failed to retract lin_act {lin_act_id}.")

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
