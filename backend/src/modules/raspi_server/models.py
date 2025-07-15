from pydantic import BaseModel

class BaseResponse(BaseModel):
    message: str

class BusStatus(BaseModel):
    status: dict[int, str]
