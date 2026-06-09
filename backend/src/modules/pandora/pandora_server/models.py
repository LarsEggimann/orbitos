from pydantic import BaseModel

class BaseResponse(BaseModel):
    message: str

class PandoraWheelState(BaseModel):
    status: str # can be anything
    position: float # position in degrees relative to home position
    velocity: float # velocity in degrees per second

class TemperatureSensorState(BaseModel):
    temperature: float # temperature in degrees Celsius

class PandoraState(BaseModel):
    wheels: dict[int, PandoraWheelState] # wheel ID (we have four wheels -> 0-3) to wheel state
    relays: dict[int, bool] # relay ID (we have six relays -> 0-5) to on/off state, e.g True = voltage applied, False = no voltage applied
    temperature_sensor: TemperatureSensorState
