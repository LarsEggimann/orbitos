from enum import Enum
from typing import Optional
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Index

from src.shared.models import BaseState, BaseSetting

class RaspiState(BaseState):
    status: str = "unknown"


class RaspiSettings(BaseSetting, table=True):
    __tablename__ = "raspi_settings"

    host: str = Field(default="raspi-server")
    port: int = Field(default=8000)
    raspi_server_app_directory: str = Field(default="~/orbitos/backend/src/modules/raspi/raspi_server")

class RaspiSettingsSet(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    raspi_server_app_directory: Optional[str] = None

class RaspiData(SQLModel, table=True):
    __tablename__ = "raspi_data"

class RaspiDataResponse(BaseModel):
    device_id: int

