from enum import Enum
from typing import Optional
from pydantic import BaseModel
from sqlmodel import Field, SQLModel

from src.shared.models import BaseState, BaseSetting, ConnectionStatus

class XY(str, Enum):
    X_AXIS = "x-axis"
    Y_AXIS = "y-axis"

class XYStagesStatus(str, Enum):
    UNKNOWN = "unknown"
    IDLE = "idle"
    MOVING = "moving"

class StageState(BaseModel):
    position: Optional[float] = None
    enabled: Optional[bool] = None
    axis_speed: Optional[float] = None
    device_number: Optional[str] = None
    current_limit_errors: Optional[str] = None
    axis_status: Optional[list] = None
    moving: Optional[bool] = None
    connection_status: ConnectionStatus = ConnectionStatus.DISCONNECTED

class XYStagesState(BaseState):
    status: XYStagesStatus = XYStagesStatus.UNKNOWN
    x_state: StageState = StageState()
    y_state: StageState = StageState()


class XYStagesSettings(BaseSetting, table=True):
    __tablename__ = "xy_stages_settings"

    x_direction_modifier: Optional[int] = Field(default=1, nullable=True)
    y_direction_modifier: Optional[int] = Field(default=1, nullable=True)


class XYStagesData(SQLModel, table=True):
    __tablename__ = "xy_stages_data"
    timestamp: float = Field(primary_key=True, index=True)
    x_position: float | None = Field(default=None, nullable=True)
    y_position: float | None = Field(default=None, nullable=True)


class XYStagesDataResponse(BaseModel):
    device_name: str = "xy_stages"
    timestamp: list[float]
    x_position: list[float | None]
    y_position: list[float | None]


class XYStagesSettingsSet(SQLModel):
    x_direction_modifier: Optional[int] = Field(default=None, nullable=True)
    y_direction_modifier: Optional[int] = Field(default=None, nullable=True)


class PerformaxUSBDevice(BaseModel):
    index: int
    description: str
