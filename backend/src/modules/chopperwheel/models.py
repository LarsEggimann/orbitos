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
    PERFORMING_FLASH_BEAM = "performing_flash_beam"
    FINDING_HOME = "finding_home"

class AngleHomeSensToBeamPipe(int, Enum):
    SMALL_WHEEL_V1 = 140


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

    flash_beam_delay: float = Field(
        default=0.1,
        description="Delay in seconds before performing flash beam operation",
    )

    angle_home_sens_to_beam_pipe: AngleHomeSensToBeamPipe = Field(
        default=AngleHomeSensToBeamPipe.SMALL_WHEEL_V1,
        description="Angle in degrees from home sensor position of the wheel to the start of beam pipe.",
    )


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


class COMPort(BaseModel):
    port: str
    description: str
