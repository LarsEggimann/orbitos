import logging
from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from .models import BaseResponse, BusStatus, LinActStatus

logger = logging.getLogger(__name__)

DEVICE_BUS = 1
DEVICE_ADDR = 0x10

# try import smbus (apt package on raspi)
try:
    import smbus # type: ignore
    # -> to install on raspi: sudo apt install -y i2c-tools python3-smbus
except ImportError:
    logger.warning("native smbus not available, using smbus3")
    import smbus3 as smbus  # use for local development

lin_act_ids = [1, 2 , 3]

# Global bus instance - initialized lazily
_bus = None

def bus() -> smbus.SMBus:
    """Get or initialize the SMBus connection."""
    global _bus
    if _bus is None:
        _bus = smbus.SMBus(DEVICE_BUS)
    return _bus

router = APIRouter(
    tags=["raspi-server"],
    prefix="/raspi-server",
)

@router.post("/{lin_act_id}/extract", response_model=BaseResponse)
def extract_lin_act(lin_act_id: int):
    """
    Switch lin act assigned to the given ID to the 'extract' position.
    """
    bus().write_byte_data(DEVICE_ADDR, lin_act_id, 0xFF)

    return BaseResponse(
        message=f"lin_act {lin_act_id} switched to extract position."
    )

@router.post("/{lin_act_id}/retract", response_model=BaseResponse)
def retract_lin_act(lin_act_id: int):
    """
    Switch lin_act assigned to the given ID to the 'retract' position.
    """
    bus().write_byte_data(DEVICE_ADDR, lin_act_id, 0x00)

    return BaseResponse(
        message=f"lin_act {lin_act_id} switched to retract position."
    )

@router.get("/status", response_model=dict[int, BusStatus])
def get_status():
    """
    Get the current status of the lin_acts.
    """
    try:
        bus_status = {}
        for lin_act_id in lin_act_ids:
            raw_value = bus().read_byte_data(DEVICE_ADDR, lin_act_id)
            
            # Interpret the raw byte value
            if raw_value == 0x00:
                status_str = LinActStatus.RETRACTED
            elif raw_value == 0xFF:
                status_str = LinActStatus.EXTRACTED
            else:
                status_str = LinActStatus.UNKNOWN
            
            bus_status[lin_act_id] = BusStatus(lin_act_id=lin_act_id, status=status_str, raw_value=raw_value)

        return bus_status
    
    except Exception as e:
        logger.error("Error reading lin_act status: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read lin_act status."
        ) from e

@router.get("/health-check", response_model=BaseResponse)
def health_check():
    """
    Get the current status of the server.
    """
    return BaseResponse(
        message="Raspi server is running and accessible."
    )
