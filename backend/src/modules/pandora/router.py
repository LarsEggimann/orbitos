import logging
import subprocess
import json

import websockets
import asyncio
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
    PandoraSettingsSet,
    PandoraState,
)

from src.modules.pandora.module import ControllerDep, PandoraClientDep
from src.modules.pandora.module import ws_manager
from src.modules.pandora.db import SessionDep

from src.modules.pandora.client.pandora_control_server_api_client.api.pandora_control_server import (
    pandora_control_server_health_check,
    pandora_control_server_get_state
)
from src.modules.pandora.client.pandora_control_server_api_client.api.pandora_wheels import (
    pandora_wheels_go_to_position,
    pandora_wheels_start_reference_search,
    pandora_wheels_stop_reference_search
)

from src.modules.pandora.pandora_server.models import PandoraState as PandoraServerState


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

@router.get("/server/health-check", response_model=BaseResponse)
async def server_health_check(client: PandoraClientDep, controller: ControllerDep):
    """
    Check if the server is running on the host.
    """
    try:
        response = await pandora_control_server_health_check.asyncio_detailed(client=client)
        if response.status_code == status.HTTP_200_OK:
            controller.state.update(connection_status=ConnectionStatus.CONNECTED)
            return response.parsed
        else:
            raise_server_error(
                f"Unexpected status code {response.status_code} from server health check, content: {response.content.decode()}"
            )
    except Exception as e:
        logger.error("Error connecting to pandora server: %s", e)
        controller.state.update(connection_status=ConnectionStatus.DISCONNECTED)
        raise_server_error("Failed to connect to pandora server.")
 
@router.get("/state", response_model=PandoraState)
async def get_state(client: PandoraClientDep, controller: ControllerDep):
    """
    Get the current state of the pandora module.
    """
    response = await pandora_control_server_get_state.asyncio_detailed(client=client)
    if response.status_code != status.HTTP_200_OK:
        logger.error("Unexpected status code %d from server state check, content: %s", response.status_code, response.content.decode())
        raise_server_error("Failed to get state from pandora server.")
    elif response.parsed is None:
        logger.error("Parsed response is None from server state check, content: %s", response.content.decode())
        raise_server_error("Failed to get state from pandora server: parsed response is None.")
    else:        
        converted_state = PandoraServerState(**response.parsed.to_dict())
        logger.info("Fetched pandora server state: %s", converted_state)
        controller.state.update(connection_status=ConnectionStatus.CONNECTED)
        controller.update_state(converted_state)
    return controller.state.get()

@router.post("/{device_id}/settings", response_model=BaseResponse)
def set_pandora_settings(
    controller: ControllerDep, settings: PandoraSettingsSet
):
    """
    Set the one or more setting of the pandora module.
    """
    controller.update_settings(settings)
    changed_fields = (
        controller.settings.get_changed_fields_compared_to_settings_before_change()
    )
    return BaseResponse(
        message=f"Settings updated for {controller.device_name}. Changed fields: {changed_fields}"
    )

@router.get("/settings", response_model=PandoraSettings)
async def get_settings(controller: ControllerDep):
    """
    Get the current settings for the pandora server.
    """
    return controller.settings.get()


# wheels control endpoints
@router.post("/wheels/{wheel_id}/go-to-position/{angle_deg}", response_model=BaseResponse)
async def go_to_position(wheel_id: int, angle_deg: float, client: PandoraClientDep):
    """
    Move the specified wheel to the given angle in degrees.
    """
    response = await pandora_wheels_go_to_position.asyncio_detailed(
        wheel_id=wheel_id, angle_deg=angle_deg, client=client
    )
    if response.status_code != status.HTTP_200_OK:
        logger.error("Unexpected status code %d from go_to_position, content: %s", response.status_code, response.content.decode())
        raise_server_error("Failed to move wheel to position.")
    return BaseResponse(message=f"Wheel {wheel_id} moving to position {angle_deg} degrees.")

@router.post("/wheels/{wheel_id}/start-reference-search", response_model=BaseResponse)
async def start_reference_search(wheel_id: int, client: PandoraClientDep):
    """
    Start the reference search for the specified wheel.
    """
    response = await pandora_wheels_start_reference_search.asyncio_detailed(
        wheel_id=wheel_id, client=client
    )
    if response.status_code != status.HTTP_200_OK:
        logger.error("Unexpected status code %d from start_reference_search, content: %s", response.status_code, response.content.decode())
        raise_server_error("Failed to start reference search for wheel.")
    return BaseResponse(message=f"Reference search started for wheel {wheel_id}.")

@router.post("/wheels/{wheel_id}/stop-reference-search", response_model=BaseResponse)
async def stop_reference_search(wheel_id: int, client: PandoraClientDep):
    """
    Stop the reference search for the specified wheel.
    """
    response = await pandora_wheels_stop_reference_search.asyncio_detailed(
        wheel_id=wheel_id, client=client
    )
    if response.status_code != status.HTTP_200_OK:
        logger.error("Unexpected status code %d from stop_reference_search, content: %s", response.status_code, response.content.decode())
        raise_server_error("Failed to stop reference search for wheel.")
    return BaseResponse(message=f"Reference search stopped for wheel {wheel_id}.")

@router.websocket("/ws")
async def pandora_ws(websocket: WebSocket, controller: ControllerDep):
    device_name = controller.device_name
    await ws_manager.connect(device_name, websocket)

    logger.info("WebSocket connection established for %s", device_name)

    # websocket url of the raspberry pi server
    pandora_server_url = f"ws://{controller.settings.get().host}:{controller.settings.get().port}/ws"

    # monitor function, exits when frontend disconnects
    async def monitor_frontend_disconnect():
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info("Frontend disconnected.")

    # connect to pandora-server websocket and forward messages to frontend, try to reconnect if connection is lost
    async def manage_raspi_stream():
        while True:
            try:
                logger.info("Attempting to connect to Pandora Server WebSocket at %s...", pandora_server_url)
                async with websockets.connect(pandora_server_url) as raspi_ws:
                    logger.info("Successfully connected to Pandora Server WebSocket!")
                    controller.state.update(connection_status=ConnectionStatus.CONNECTED)

                    async for message in raspi_ws:
                        # TODO: implement some form of differenctiation between state and data updates in future maybe we want to store position and velocity data in the database
                        # for now we just assume its a state update, try to parse it and update the controller state, which will then broadcast to all frontend monitors via the on_state_update callback in the controller

                        # await websocket.send_text(message)
                        # try to parse this and make sure we have the "type": "state" field
                        # if it's a state update, we also want to update the controller state so it gets broadcasted to all frontend monitors
                        has_type_field = False
                        try:
                            message_dict = json.loads(message)
                            has_type_field = "type" in message_dict
                            if has_type_field and message_dict["type"] == "state":
                                converted_state = PandoraServerState(**message_dict["content"])
                                controller.update_state(converted_state)
                        except json.JSONDecodeError:
                            logger.warning("Received non-JSON message from Pandora Server WebSocket: %s", message)
                        except Exception as e:
                            logger.error("Error processing message from Pandora Server WebSocket: %s", e)

            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError, OSError) as e:
                logger.warning("Pandora Server unavailable or disconnected (%s). Retrying in 10 seconds...", type(e).__name__)
                try:
                    controller.state.update(connection_status=ConnectionStatus.DISCONNECTED)
                except Exception:
                    pass
                await asyncio.sleep(10) # wait before retrying

    # r the frontend monitor and the Pandora Server stream together
    done, pending = await asyncio.wait(
        [
            asyncio.create_task(monitor_frontend_disconnect()),
            asyncio.create_task(manage_raspi_stream()),
        ],
        return_when=asyncio.FIRST_COMPLETED,
    )

    # if the frontend disconnects, it kills the infinite Pandora Server retry loop here
    for task in pending:
        task.cancel()

    await ws_manager.disconnect(device_name, websocket)
    logger.info("Cleaned up connections for %s", device_name)

