from typing import Optional
from pydantic import BaseModel, Field

class BaseResponse(BaseModel):
    message: str

class PandoraWheelState(BaseModel):
    status: str = "unknown" # can be anything
    position: Optional[float] = None # position in degrees relative to home position
    velocity: Optional[float] = None # velocity in degrees per second

class TemperatureSensorState(BaseModel):
    temperature: Optional[float] = None # temperature in degrees Celsius

class PandoraState(BaseModel):
    wheels: dict[int, PandoraWheelState] = Field(default_factory=dict) # wheel ID (we have four wheels -> 0-3) to wheel state
    relays: dict[int, bool] = Field(default_factory=dict) # relay ID (we have six relays -> 0-5) to on/off state, e.g True = voltage applied, False = no voltage applied
    temperature_sensor: TemperatureSensorState = Field(default_factory=TemperatureSensorState)
