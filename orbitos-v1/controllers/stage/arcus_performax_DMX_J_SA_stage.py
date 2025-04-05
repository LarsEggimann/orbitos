#!/usr/bin/env python3

import logging
from pathlib import Path

from pylablib.devices import Arcus  # type: ignore
import pylablib as pll  # type: ignore
import asyncio


logger = logging.getLogger()
work_dir = Path(__file__).parent


class ArcusPerformaxDMXJSAStage:
    def __init__(self, name):

        self.STEPS_PER_MM = 800
        self.STEPS_PER_FULL_ROTATION = 3200
        self.STEPS_PER_SECOND_TO_MMPS = 1 / self.STEPS_PER_MM
        self.STEPS_PER_SECOND_RPS = 1 / self.STEPS_PER_FULL_ROTATION

        # setting the path to the dll
        pll.par["devices/dlls/arcus_performax"] = str(work_dir / "dll")

        self.dev: Arcus.PerformaxDMXJSAStage = None  # type: ignore

        self.position = None
        self.status = None
        self.enabled = None
        self.axis_speed = None
        self.device_number = None
        self.current_limit_errors = None
        self.axis_status = None
        self.moving = None

        self.connected = False

        self.name = name

    async def update_pos_while_moving(self):
        while self.dev.is_moving():
            self.position = self.get_position()
            await asyncio.sleep(0.1)

    def get_axis_speed(self):
        return self.dev.get_axis_speed() * self.STEPS_PER_SECOND_TO_MMPS

    def set_axis_speed(self, speed_in_mm_per_s):
        self.dev.set_axis_speed(int(speed_in_mm_per_s / self.STEPS_PER_SECOND_TO_MMPS))

    def set_zero(self):
        self.dev.set_position_reference(0)

    def move_by(self, dist_in_mm):
        self.dev.move_by(int(dist_in_mm * self.STEPS_PER_MM))
        asyncio.create_task(self.update_pos_while_moving())

    def move_to(self, pos_in_mm):
        self.dev.move_to(int(pos_in_mm * self.STEPS_PER_MM))
        asyncio.create_task(self.update_pos_while_moving())

    def get_full_status(self):
        self.status = self.dev.get_full_status()
        self.enabled = self.status["enabled"]
        self.axis_speed = self.status["axis_speed"] * self.STEPS_PER_SECOND_TO_MMPS
        self.device_number = self.status["device_number"]
        self.current_limit_errors = self.status["current_limit_errors"]
        # check if string is empty
        if self.current_limit_errors:
            match self.current_limit_errors:
                case "+":
                    self.current_limit_errors = "Limit in positive direction reached"
                case "-":
                    self.current_limit_errors = "Limit in negative direction reached"

        self.set_position(self.status["position"])
        self.axis_status = self.status["axis_status"]
        self.moving = self.status["moving"]
        return self.status

    def set_position(self, pos_in_steps):
        self.position = float(pos_in_steps) / float(self.STEPS_PER_MM)

    def get_position(self):
        return self.dev.get_position() / float(self.STEPS_PER_MM)

    def is_healthy(self):
        try:
            self.get_full_status()
            self.connected = True
            return True
        except Exception as e:
            self.connected = False
            logger.error(f"Error during health check in {self.name}: {e}")
            return False

    def close(self):
        if self.dev is not None:
            self.dev.close()
            self.connected = False

    def connect(self, idx=0):
        self.dev = Arcus.PerformaxDMXJSAStage(idx)
        self.dev.open()
        self.status = self.get_full_status()
        self.connected = True

    def list_usb_performax_devices(self):
        list_dev_names = {}
        try:
            for dev in Arcus.list_usb_performax_devices():
                # list_dev_names.append(tuple((dev[0], dev[1])))
                list_dev_names[dev[0]] = dev[1]
        except Exception as e:
            logger.error(f"Error during listing USB devices: {e}")
        return list_dev_names
