from enum import Enum
from typing import Optional
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Index

from src.shared.models import BaseState, BaseSetting


class ElectrometerStatus(str, Enum):
    UNKNOWN = "unknown"
    IDLE = "idle"
    TRIGGER_BASED_MEASUREMENT_RUNNING = "trigger_based_measurement_running"
    FETCHING_TRIGGER_BASED_MEASUREMENT_DATA = "fetching_trigger_based_measurement_data"
    WAITING_TO_START_CONTINUOUS_MEASUREMENT = "waiting_to_start_continuous_measurement"
    CONTINUOUS_MEASUREMENT_RUNNING = "continuous_measurement_running"


class ElectrometerName(str, Enum):
    electrometer_1 = "electrometer_1"
    electrometer_2 = "electrometer_2"


class ElectrometerState(BaseState):
    status: ElectrometerStatus = ElectrometerStatus.UNKNOWN
    trigger_based_measurement_status: str = "unknown"
    source_voltage_status: str = "unknown"
    output_status: str = "unknown"
    input_status: str = "unknown"


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

    voltage_start: float = Field(default=0.0)
    voltage_stop: float = Field(default=10.0)
    voltage_step: float = Field(default=1)
    voltage_settle_time: float = Field(default=1)

class ElectrometerData(SQLModel, table=True):
    __tablename__ = "electrometer_data"
    device_id: int = Field(primary_key=True, index=True)
    timestamp: float = Field(primary_key=True, index=True)
    current: float = Field(default=0.0, lt=1e35)

    __table_args__ = (Index("idx_device_time", "device_id", "timestamp"),)


class ElectrometerDataResponse(BaseModel):
    device_name: ElectrometerName
    current: list[float]
    timestamp: list[float]


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

    voltage_start: Optional[float] = None
    voltage_stop: Optional[float] = None
    voltage_step: Optional[float] = None
    voltage_settle_time: Optional[float] = None
