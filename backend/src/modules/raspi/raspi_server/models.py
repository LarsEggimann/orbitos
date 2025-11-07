from enum import Enum
from pydantic import BaseModel
from typing import Optional

class BaseResponse(BaseModel):
    message: str

class LinActStatus(str, Enum):
    EXTENDED = "extended"
    RETRACTED = "retracted"
    UNKNOWN = "unknown"

class BusStatus(BaseModel):
    lin_act_id: int
    status: LinActStatus
    raw_value: Optional[int] = None  # Optional raw value for debugging
