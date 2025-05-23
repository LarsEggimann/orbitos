from fastapi import APIRouter, Depends
import time

from src.modules.electrometer.models import ElectrometerState
from src.modules.electrometer.module import ControllerDep

router = APIRouter(
    tags=["electrometer"],
    prefix="",
)

@router.post("/{device_id}/connect/{ip}", response_model=ElectrometerState)
def connect_to_electrometer(ip: str, controller: ControllerDep):
    """
    Connect to the electrometer with the given device ID.
    """
    print(f"Connecting to electrometer with IP: {ip}")
    print(f"Controller: {controller}")
    print(f"Controller device ID: {controller.device_id.value}")
    return controller.connect_to_keysight_em(ip)
