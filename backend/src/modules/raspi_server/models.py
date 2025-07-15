from enum import Enum
from pydantic import BaseModel
from typing import Optional

class BaseResponse(BaseModel):
    message: str

class ValveStatus(str, Enum):
    EXTRACTED = "extracted"
    RETRACTED = "retracted"
    UNKNOWN = "unknown"

class BusStatus(BaseModel):
    valve_id: int
    status: ValveStatus
    raw_value: Optional[int] = None  # Optional raw value for debugging
