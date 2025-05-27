from datetime import datetime
from typing import Optional, Any
from enum import Enum
from sqlmodel import Field, SQLModel
from pydantic import BaseModel


class WebSocketMessageType(str, Enum):
    STATE = "state"
    DATA = "data"
    ERROR = "error"
    INFO = "info"


class BaseWebSocketMessage(BaseModel):
    type: WebSocketMessageType
    device_id: str
    content: Optional[Any] = None


class BaseResponse(BaseModel):
    message: str
    error: Optional[str] = None


class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    HEALTH_CHECK_FAILED = "health check failed"


class BaseState(SQLModel):
    """
    Base class for all state models.
    """

    device_id: str = Field(primary_key=True, index=True)

    status: Optional[str] = Field(default=None)
    connection_status: ConnectionStatus = Field(default=ConnectionStatus.DISCONNECTED)
    error: Optional[str] = Field(default=None)


class TimeFrameInput(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
