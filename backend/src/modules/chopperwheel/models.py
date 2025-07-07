from enum import Enum
from typing import Optional
from pydantic import BaseModel
from sqlmodel import Field, SQLModel

from src.shared.models import BaseState, BaseSetting


class CWStatus(str, Enum):
    UNKNOWN = "unknown"
    IDLE = "idle"
    ROTATING = "rotating"
    ROTATE_DEMO_RUNNING = "rotate_demo_running"


class CWState(BaseState):
    status: CWStatus = CWStatus.UNKNOWN


class CWSettings(BaseSetting, table=True):
    __tablename__ = "chopper_wheel_settings"

    max_velocity: float = Field(default=2.0, description="Maximum velocity in rps")
    max_acceleration: float = Field(
        default=1.0, description="Maximum acceleration in rps^2"
    )

    max_current: int = Field(default=150, le=255, description="Maximum current [0-255]")
    standby_current: int = Field(
        default=0, le=255, description="Standby current [0-255]"
    )
    boost_current: int = Field(default=0, le=255, description="Boost current [0-255]")


class CWData(SQLModel, table=True):
    __tablename__ = "chopper_wheel_data"
    timestamp: float = Field(primary_key=True, index=True)
    velocity: float = Field(default=None, nullable=True)
    angular_position: float = Field(default=None, nullable=True)


class CWDataResponse(BaseModel):
    device_name: str = "chopper_wheel"
    timestamp: list[float]
    velocity: list[float]
    angular_position: list[float]


class CWSettingsSet(SQLModel):
    max_velocity: Optional[float] = None
    max_acceleration: Optional[float] = None
    max_current: Optional[float] = None
    standby_current: Optional[float] = None
    boost_current: Optional[float] = None
