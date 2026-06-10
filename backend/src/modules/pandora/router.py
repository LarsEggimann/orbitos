import logging
import subprocess

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


@router.websocket("/ws")
async def pandora_ws(websocket: WebSocket, controller: ControllerDep):
    device_name = controller.device_name
    await ws_manager.connect(device_name, websocket)
    logger.info("WebSocket connection established for %s", device_name)

    # This dummy listener monitors the client socket for a disconnect event
    async def listen_for_client_disconnect():
        try:
            while True:
                # Keep reading to catch if the client closes the connection
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info("Client %s explicitly disconnected.", device_name)

    # This listens to the remote Pandora server and updates the state
    async def listen_to_pandora_server():
        pandora_url = f"ws://{controller.settings.get().host}:{controller.settings.get().port}/ws"
        try:
            async with websockets.connect(pandora_url) as pandora_server_ws:
                logger.info("Connected to pandora server websocket at %s", pandora_url)
                while True:
                    message = await pandora_server_ws.recv()
                    try:
                        pandora_server_state = PandoraServerState.model_validate_json(message)
                        logger.info("Received websocket message from pandora server: %s", pandora_server_state)
                        
                        # Update the state (which triggers the broadcast safely)
                        controller.update_state(pandora_server_state)
                    except Exception as e:
                        logger.error("Error parsing message from pandora server: %s", e)
        except Exception as e:
            logger.error("Lost connection to remote Pandora server: %s", e)

    try:
        # Run both tasks concurrently. If either task finishes or encounters 
        # an error (like a disconnect), the other will be cancelled automatically.
        await asyncio.gather(
            listen_for_client_disconnect(),
            listen_to_pandora_server(),
            return_exceptions=False
        )
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        # Ensure cleanup happens no matter which side disconnected
        logger.info("Cleaning up WebSocket connection for %s", device_name)
        await ws_manager.disconnect(device_name, websocket)
    # try:
    #     logger.info("WebSocket connection established for %s", device_name)

    #     # Build the external server URL
    #     pandora_server_websocket_url = f"ws://{controller.settings.get().host}:{controller.settings.get().port}/ws"
        
    #     # Connect to the remote Pandora WebSocket server using the 'websockets' library
    #     async with websockets.connect(pandora_server_websocket_url) as pandora_server_ws:
    #         logger.info("Connected to pandora server websocket at %s", pandora_server_websocket_url)
            
    #         while True:
    #             # 'websockets' uses .recv() instead of .receive_text()
    #             message = await pandora_server_ws.recv() 
                
    #             try:
    #                 pandora_server_state = PandoraServerState.model_validate_json(message)
    #                 logger.info("Received websocket message from pandora server: %s", pandora_server_state)
    #                 controller.update_state(pandora_server_state)
    #             except Exception as e:
    #                 logger.error(
    #                     "Error parsing websocket message from pandora server: %s. Message: %s. Error: %s", 
    #                     device_name, message, e
    #                 )
    # try:
    #     logger.info("WebSocket connection established for %s", device_name)

    #     # while a websocket connection is open we connect to the websocket of the pandora server and forward any messages received there to the state manager of this module, so that the state is always up to date with the actual state of the server
    #     pandora_server_websocket_url = f"ws://{controller.settings.get().host}:{controller.settings.get().port}/ws"
    #     async with httpx.AsyncClient() as http_client:
    #         async with http_client.ws_connect(pandora_server_websocket_url) as pandora_server_ws:
    #             logger.info("Connected to pandora server websocket at %s", pandora_server_websocket_url)
    #             while True:
    #                 message = await pandora_server_ws.receive_text()
    #                 try:
    #                     pandora_server_state = PandoraServerState.model_validate_json(message)
    #                     logger.info("Received websocket message from pandora server: %s", pandora_server_state)
    #                     controller.update_state(pandora_server_state)
    #                 except Exception as e:
    #                     logger.error("Error parsing websocket message from pandora server: %s. Message: %s. Error: %s", device_name, message, e)
    #                     # if we fail to parse the message, we will ignore it and not update the state, but we will log the error

    #     # while True:
    #     #     message = await websocket.receive_text()
    #     #     # any message recieved from the client will be a PandoraServerState object in JSON format, which we will parse and use to update the state of the controller
    #     #     try:
    #     #         pandora_server_state = PandoraServerState.model_validate_json(message)
    #     #         logger.info("Received websocket message from %s: %s", device_name, pandora_server_state)
    #     #         controller.update_state(pandora_server_state)
    #     #     except Exception as e:
    #     #         logger.error("Error parsing websocket message from %s: %s. Error: %s", device_name, message, e)
    #     #         # if we fail to parse the message, we will ignore it and not update the state, but we will log the error

    #     #     logger.info("Received websocket message from %s: %s", device_name, message)

    # except WebSocketDisconnect:
    #     await ws_manager.disconnect(device_name, websocket)
