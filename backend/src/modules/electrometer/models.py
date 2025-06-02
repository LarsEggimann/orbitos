from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Index

from src.shared.models import BaseState, BaseSetting


class ElectrometerStatus(str, Enum):
    UNKNOWN = "unknown"
    IDLE = "idle"
    TRIGGER_BASED_MEASUREMENT_RUNNING = "trigger_based_measurement_running"
    CONTINUOUS_MEASUREMENT_WAITING_TO_START = "continuous_measurement_waiting_to_start"
    CONTINUOUS_MEASUREMENT_RUNNING = "continuous_measurement_running"


class ElectrometerID(str, Enum):
    electrometer_1 = "electrometer_1"
    electrometer_2 = "electrometer_2"


class ElectrometerState(BaseState):
    status: ElectrometerStatus = ElectrometerStatus.UNKNOWN


class ElectrometerSettings(BaseSetting, table=True):
    __tablename__ = "electrometer_settings"

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
    device_id: str
    current: list[float]
    time: list[datetime]


class ElectrometerSettingsSet(SQLModel):
    trigger_count: Optional[int] = None
    trigger_time_interval: Optional[float] = None
    trigger_bypass: Optional[str] = None
    trigger_delay: Optional[float] = None

    function: Optional[str] = None

    aperture_integration_time: Optional[float] = None
    aperture_auto: Optional[str] = None

    current_range: Optional[float] = None
    current_range_auto: Optional[str] = None
    current_range_auto_upper_limit: Optional[float] = None
    current_range_auto_lower_limit: Optional[float] = None
