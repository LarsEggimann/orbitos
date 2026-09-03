from typing import Optional
from pydantic import BaseModel
from sqlmodel import Field, SQLModel

from src.shared.models import BaseState, BaseSetting
from src.modules.pandora.pandora_server.models import (
    PandoraState as PandoraServerState,
)

class PandoraState(PandoraServerState, BaseState):
    pass

class PandoraSettings(BaseSetting, table=True):
    __tablename__ = "pandora_settings"

    host: str = Field(default="pandora-server")
    port: int = Field(default=8000)
    pandora_server_app_directory: str = Field(default="~/orbitos/backend/src/modules/pandora/pandora_server")

class PandoraData(SQLModel, table=True):
    __tablename__ = "pandora_data"
    device_id: int = Field(primary_key=True, index=True)

class PandoraDataResponse(BaseModel):
    device_id: int

class PandoraSettingsSet(SQLModel):
    host: Optional[str] = None
    port: Optional[int] = None
    pandora_server_app_directory: Optional[str] = None