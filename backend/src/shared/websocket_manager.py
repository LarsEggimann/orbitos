import logging
from typing import Dict, List, TypeVar, Generic
import asyncio
from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from src.shared.models import BaseState, BaseWebSocketMessage, WebSocketMessageType
from src.shared.utils import run_async_in_background

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseState)
G = TypeVar("G", bound=BaseModel)


class WebSocketManager(Generic[T, G]):
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, device_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            if device_id not in self.active_connections:
                self.active_connections[device_id] = []
            self.active_connections[device_id].append(websocket)

    async def disconnect(self, device_id: str, websocket: WebSocket):
        async with self.lock:
            if device_id in self.active_connections:
                self.active_connections[device_id].remove(websocket)
                if not self.active_connections[device_id]:
                    del self.active_connections[device_id]

    async def broadcast_state(self, device_id: str, state: T):
        message = BaseWebSocketMessage(
            type=WebSocketMessageType.STATE,
            device_id=device_id,
            content=state.model_dump(),
        )
        async with self.lock:
            for ws in self.active_connections.get(device_id, []):
                try:
                    await ws.send_json(jsonable_encoder(message))
                except Exception as e:
                    logger.exception(
                        "Failed to send state to %s websocket, error %s", device_id, e
                    )

    async def broadcast_data(self, device_id: str, data: G):
        message = BaseWebSocketMessage(
            type=WebSocketMessageType.DATA,
            device_id=device_id,
            content=data.model_dump(),
        )
        async with self.lock:
            for ws in self.active_connections.get(device_id, []):
                try:
                    await ws.send_json(jsonable_encoder(message))
                except Exception as e:
                    logger.exception(
                        "Failed to send data to %s websocket, error %s", device_id, e
                    )

    def broadcast_state_sync(self, device_id: str, state: T):
        run_async_in_background(self.broadcast_state(device_id, state))

    def broadcast_data_sync(self, device_id: str, data: G):
        run_async_in_background(self.broadcast_data(device_id, data))
