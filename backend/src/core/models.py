from datetime import datetime
from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class BaseState(SQLModel):
    """
    Base class for all state models.
    """
    status: str | None = Field(default=None)
    connection_status: str | None = Field(default=None)
    error: str | None = Field(default=None)


