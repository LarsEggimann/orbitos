import logging
from typing import Dict, List, TypeVar, Generic
import asyncio
from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from src.shared.models import (
    BaseState,
    BaseWebSocketMessage,
    WebSocketMessageType,
    BaseSetting,
)
from src.shared.utils import run_async_in_background

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseState)  # state model type
G = TypeVar("G", bound=BaseModel)  # data model type
H = TypeVar("H", bound=BaseSetting)  # setting model type


class WebSocketManager(Generic[T, G, H]):
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, device_name: str, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            if device_name not in self.active_connections:
                self.active_connections[device_name] = []
            self.active_connections[device_name].append(websocket)

    async def disconnect(self, device_name: str, websocket: WebSocket):
        async with self.lock:
            if device_name in self.active_connections:
                self.active_connections[device_name].remove(websocket)
                if not self.active_connections[device_name]:
                    del self.active_connections[device_name]

    async def _broadcast_message(self, device_name: str, message: BaseWebSocketMessage):
        async with self.lock:
            if device_name in self.active_connections:
                for ws in self.active_connections[device_name]:
                    try:
                        await ws.send_json(jsonable_encoder(message))
                    except Exception as e:
                        logger.exception(
                            "Failed to send message to %s websocket, error %s",
                            device_name,
                            e,
                        )

    async def broadcast_state(self, device_name: str, state: T):
        message = BaseWebSocketMessage(
            type=WebSocketMessageType.STATE,
            device_name=device_name,
            content=state.model_dump(),
        )
        await self._broadcast_message(device_name, message)

    async def broadcast_data(self, device_name: str, data: G):
        message = BaseWebSocketMessage(
            type=WebSocketMessageType.DATA,
            device_name=device_name,
            content=data.model_dump(),
        )
        await self._broadcast_message(device_name, message)

    async def broadcast_setting(self, device_name: str, setting: H):
        message = BaseWebSocketMessage(
            type=WebSocketMessageType.SETTINGS,
            device_name=device_name,
            content=setting.model_dump(),
        )
        await self._broadcast_message(device_name, message)

    def broadcast_state_sync(self, device_name: str, state: T):
        run_async_in_background(self.broadcast_state(device_name, state))

    def broadcast_data_sync(self, device_name: str, data: G):
        run_async_in_background(self.broadcast_data(device_name, data))

    def broadcast_setting_sync(self, device_name: str, setting: H):
        run_async_in_background(self.broadcast_setting(device_name, setting))
