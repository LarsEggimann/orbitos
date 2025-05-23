from typing import Optional
from enum import Enum
from sqlmodel import Field, SQLModel


class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
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
