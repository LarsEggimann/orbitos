from datetime import datetime
from pydantic import BaseModel
from enum import Enum
from sqlmodel import Field, SQLModel, Index

from src.core.models import BaseState


class ElectrometerID(str, Enum):
    EM_1 = "electrometer_1"
    EM_2 = "electrometer_2"


class ElectrometerState(BaseState, table=True):
    __tablename__ = "electrometer_state"

    trigger_count: int = Field(default=100)
    trigger_time_interval: float = Field(default=0.1)
    trigger_bypass: str = Field(default="OFF")
    trigger_delay: float = Field(default=0.0)

    function: str = Field(default="CURR")

    aperture_integration_time: float = Field(default=0.2)
    aperture_auto: str = Field(default="OFF")

    current_range: float = Field(default=100e-9)
    current_range_auto: str = Field(default="ON")
    current_range_auto_upper_limit: float = Field(default=1e-7)
    current_range_auto_lower_limit: float = Field(default=1e-16)


class CurrentData(SQLModel, table=True):
    __tablename__ = "electrometer_data"
    device_id: ElectrometerID = Field(primary_key=True, index=True)
    time: float = Field(primary_key=True, index=True)
    current: float = Field(default=0.0, le=1e35)

    __table_args__ = (Index("idx_device_time", "device_id", "time"),)


class CurrentDataResponse(BaseModel):
    current: list[float]
    time: list[datetime]
