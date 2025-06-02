from datetime import datetime
from typing import Optional, Any
from enum import Enum
from sqlmodel import Field, SQLModel
from pydantic import BaseModel


class WebSocketMessageType(str, Enum):
    STATE = "state"
    DATA = "data"
    SETTINGS = "settings"


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


class BaseState(BaseModel):
    """
    Base class for all state models.
    """

    device_id: str
    status: str = "unknown"
    connection_status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    error: Optional[str] = None


class BaseSetting(SQLModel):
    """
    Base class for all setting models.
    """

    device_id: str = Field(primary_key=True, index=True)


class TimeFrameInput(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
