import logging
from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
import smbus # sudo apt install -y i2c-tools python3-smbus
# import smbus3 as smbus  # use for local development
from .models import BaseResponse, BusStatus

logger = logging.getLogger(__name__)

DEVICE_BUS = 1
DEVICE_ADDR = 0x10
bus = smbus.SMBus(DEVICE_BUS)  # Initialize the I2C bus

valve_ids = [1, 2 , 3]

router = APIRouter(
    tags=["raspi-server"],
    prefix="/raspi-server",
)

@router.post("/{valve_id}/extract", response_model=BaseResponse)
def extract_valve(valve_id: int):
    """
    Switch valve assigned to the given ID to the 'extract' position.
    """
    bus.write_byte_data(DEVICE_ADDR, valve_id, 0xFF)


    return BaseResponse(
        message=f"Valve {valve_id} switched to extract position."
    )

@router.post("/{valve_id}/retract", response_model=BaseResponse)
def retract_valve(valve_id: int):
    """
    Switch valve assigned to the given ID to the 'retract' position.
    """
    bus.write_byte_data(DEVICE_ADDR, valve_id, 0x00)

    return BaseResponse(
        message=f"Valve {valve_id} switched to retract position."
    )

@router.get("/status", response_model=list[BusStatus])
def get_status():
    """
    Get the current status of the valves.
    """
    try:
        bus_status = []
        for valve_id in valve_ids:
            raw_value = bus.read_byte_data(DEVICE_ADDR, valve_id)
            
            # Interpret the raw byte value
            if raw_value == 0x00:
                status_str = ValveStatus.RETRACTED
            elif raw_value == 0xFF:
                status_str = ValveStatus.EXTRACTED
            else:
                status_str = ValveStatus.UNKNOWN
            
            bus_status.append(BusStatus(valve_id=valve_id, status=status_str, raw_value=raw_value))

        return bus_status
    
    except Exception as e:
        logger.error("Error reading valve status: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read valve status."
        ) from e

