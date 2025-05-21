from datetime import datetime
from pydantic import BaseModel
from sqlmodel import Field, SQLModel

from src.core.models import BaseState

class ElectrometerState(BaseState, table=True):
    __tablename__ = "em_state"
    id: str = Field(primary_key=True, index=True)

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
    __tablename__ = "em_current_data"
    time: float = Field(primary_key=True, index=True)
    current: float = Field(default=0.0, le=1e35)


class CurrentDataResponse(BaseModel):
    current: list[float]
    time: list[datetime]
