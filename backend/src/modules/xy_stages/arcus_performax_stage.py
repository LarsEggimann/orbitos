#!/usr/bin/env python3

import logging
from pathlib import Path

from pylablib.devices import Arcus  # type: ignore
import pylablib as pll  # type: ignore
import threading

from src.shared.models import ConnectionStatus
from src.modules.xy_stages.models import PerformaxUSBDevice, StageState


logger = logging.getLogger(__name__)
work_dir = Path(__file__).parent



# decorator to synchronize access to methods to serial interface and motor
# methods annotated with this decorator will acquire a lock before executing and keep it until the method returns
# this ensures that only one thread can access the serial interface and motor at a time AND more importantly
# waits for the connection to respond before releasing the lock
def synchronized(lock_attr="_lock"):
    def decorator(method):
        def wrapper(self, *args, **kwargs):
            lock = getattr(self, lock_attr)
            with lock:
                return method(self, *args, **kwargs)

        return wrapper

    return decorator


class ArcusPerformaxStage:
    def __init__(self, name, direction_modifier=1):

        self.STEPS_PER_MM = 800
        self.STEPS_PER_FULL_ROTATION = 3200
        self.STEPS_PER_SECOND_TO_MMPS = 1 / self.STEPS_PER_MM
        self.STEPS_PER_SECOND_RPS = 1 / self.STEPS_PER_FULL_ROTATION

        # setting the path to the dll
        pll.par["devices/dlls/arcus_performax"] = str(work_dir / "dll")

        self.dev: Arcus.PerformaxDMXJSAStage = None  # type: ignore

        self.state: StageState = StageState() # type: ignore

        self.name = name

        self._lock = threading.RLock()  # allow same thread to acquire the lock multiple times, used in synchronized() decorator

        self.direction_modifier = direction_modifier

    @synchronized()
    def set_zero(self):
        self.dev.set_position_reference(0)

    @synchronized()
    def move_by(self, dist_in_mm):
        self.dev.move_by(self.direction_modifier * int(dist_in_mm * self.STEPS_PER_MM))

    @synchronized()
    def move_to(self, pos_in_mm):
        self.dev.move_to(self.direction_modifier * int(pos_in_mm * self.STEPS_PER_MM))

    @synchronized()
    def get_full_stage_state(self) -> StageState:
        if self.dev is None:
            return StageState()
        try:
            s = self.dev.get_full_status()

            print(f"Full status: {s}")
            clm = s["current_limit_errors"]
            if clm:
                if clm == "+":
                    clm = "Limit in positive direction reached"
                elif clm == "-":
                    clm = "Limit in negative direction reached"
                else:
                    clm = "Unknown current limit error"

            self.state = StageState(
                position=self._to_mm(s["position"]),
                enabled=s["enabled"],
                axis_speed=self._to_mmps(s["axis_speed"]),
                device_number=s["device_number"],
                current_limit_errors=clm,
                axis_status=s["axis_status"],
                moving=s["moving"],
                connection_status=ConnectionStatus.CONNECTED if self.dev.is_opened() else ConnectionStatus.DISCONNECTED,
            )
        except Exception as e:
            logger.error("Error getting full status: %s", e)
            self.state = StageState()
            
        return self.state

    def _to_mm(self, pos_in_steps):
        return self.direction_modifier * float(pos_in_steps) / float(self.STEPS_PER_MM)
    
    def _to_mmps(self, speed_in_steps):
        return self.direction_modifier * float(speed_in_steps) * self.STEPS_PER_SECOND_TO_MMPS

    @synchronized()
    def close(self):
        if self.dev is not None:
            self.dev.close()
            self.state = StageState()
            self.dev = None
        logger.info("Closed connection to Performax stage %s", self.name)

    @synchronized()
    def connect(self, idx=0):
        self.dev = Arcus.PerformaxDMXJSAStage(idx)
        self.dev.open()
        self.state = self.get_full_stage_state()
        logger.info("Connected to Performax stage %s with index %d, state %s", self.name, idx, self.state)

    @synchronized()
    def list_usb_performax_devices(self):
        """
        Get the available Performax USB Devices for the xy stages.

        Returns:
            A list of available Performax USB Devices.
        """
        ports: list[PerformaxUSBDevice] = []
        try:
            for dev in Arcus.list_usb_performax_devices():
                print(f"Found USB device: {dev}")
                new_port = PerformaxUSBDevice(
                    index=dev[0], description=str(dev[1] + " " + dev[2])
                )
                ports.append(new_port)
        except Exception as e:
            logger.error("Error during listing USB devices: %s", e)
        return ports
