#!/usr/bin/env python3
"""
This module represents a chopper wheel device.
"""
import asyncio
import csv
import logging
import os
import time
from multiprocessing.connection import Connection
from typing import Callable

from pytrinamic.connections import ConnectionManager  # type: ignore
from pytrinamic.modules import TMCM1021  # type: ignore
from util.controller_base import ControllerBase
from util.settings_handler import SettingsHandler

logger = logging.getLogger()


class ChopperWheel(ControllerBase):

    def __init__(
        self, address: str, pipe: Connection, settings_handler: SettingsHandler
    ) -> None:
        """
        Initializes a ChopperWheel instance.

        Args:
            interface_args: The interface arguments for connecting to the device.
        """
        super().__init__(address, pipe, settings_handler)

        self.timestamp: list[float] = []
        self.velocity_list: list[float] = []
        self.angular_position_list: list[float] = []

        self.free_rot_angle = 290  # degrees

        self.wait_time_after_rotation = 0  # seconds
        self.interface_args = (
            f"--interface serial_tmcl --port {self.address} --data-rate 9600"
        )

        self.microstep_resolution = 256
        self.real_steps_per_rotation = 200
        self.steps_per_rotation = (
            self.real_steps_per_rotation * self.microstep_resolution
        )

        self.direction_modifier = -1

        try:
            self.connect()
            self.initialize_motor_settings()
        except Exception as e:
            logger.error("Could not connect to the device.")
            logger.error(e)
            self.pipe.send(e)

        self.listening_starter()

    def listening_starter(self):
        try:
            asyncio.run(self.start_listening())
        except Exception as e:
            logger.warning(
                "Exception occurred in start_listening() method. emptying pipe..."
            )
            logger.error(e)
            time.sleep(0.5)
            self.clear_pipe()
            time.sleep(0.5)
            logger.warning("restart the listening loop")
            self.listening_starter()

    async def start_listening(self):
        logger.info("Chopper Wheel Controller is listening for commands.")

        loop = asyncio.get_event_loop()
        loop.create_task(self.send_status_data())

        while True:

            # pipe.revc is blocking, so we need to run it in a separate thread to not block the event loop
            # threads produce a lot of overhead, so this is only fine as long as we dont recieve a lot of commands within seconds
            received_command: str = await loop.run_in_executor(None, self.pipe.recv)
            command: str = received_command.split(" ")[0]

            match command:
                case "one_rotation":
                    logger.info("Received command: one_rotation")
                    await self.exec_rotation_command(self.one_rotation)
                case "rotate_demo":
                    logger.info("Received command: rotate_demo")
                    await self.exec_rotation_command(self.rotate_demo)
                case "one_flash_please":
                    logger.info("Received command: one_flash_please")
                    await self.exec_rotation_command(self.one_flash_please)
                case "find_home":
                    logger.info("Received command: find_home")
                    await self.exec_rotation_command(self.find_home)
                case "get_settings":
                    self.print_settings()
                case "settings_changed":
                    self.settings_changed()
                case "exit":
                    logger.info("exiting...")
                    break
                case _:
                    logger.info("Unknown command")

    def settings_changed(self):
        self.settings_handler.read_settings()
        changed_settings = self.settings_handler.get_changed_settings()
        for setting, value in changed_settings.items():
            match setting:
                case "max_velocity":
                    self.set_max_velocity(value)
                    logger.info("Setting max_velocity to %s", value)
                case "max_acceleration":
                    self.set_acceleration(value)
                    logger.info("Setting max_acceleration to %s", value)
                case "max_current":
                    self.motor.drive_settings.max_current = value
                    logger.info("Setting max_current to %s", value)

    async def exec_rotation_command(self, func: Callable):
        acquire_data_task = asyncio.create_task(self.acquire_data())

        await asyncio.sleep(0.1)

        send_data_task = asyncio.create_task(self.save_data())
        await func()
        acquire_data_task.cancel()
        await asyncio.sleep(0.2)
        send_data_task.cancel()

    async def save_data(self):
        while True:
            await self.save_data_to_file()
            await asyncio.sleep(0.2)

    def print_settings(self):
        print(
            {
                "max_velocity": self.get_max_velocity(),
                "max_acceleration": self.get_max_acceleration(),
                "max_current": self.motor.drive_settings.max_current,
                "standby_current": self.motor.drive_settings.standby_current,
                "boost_current": self.motor.drive_settings.boost_current,
                "filename": self.settings_handler.settings["filename"],
            }
        )

    async def send_status_data(self):
        while True:
            self.pipe.send(
                {
                    "status_data": {
                        "are_we_home_yet": self.are_we_home_yet(),
                    },
                    "healthy": await self.health_check(),
                }
            )
            await asyncio.sleep(self.send_status_data_timeout)

    async def save_data_to_file(self):
        if not os.path.isfile(self.settings_handler.settings["filename"]):
            logger.warning("File does not exist, data not saved")
            return

        with open(
            self.settings_handler.settings["filename"],
            "a",
            newline="",
            encoding="utf-8",
        ) as f:
            writer = csv.writer(f)
            writer.writerows(
                zip(self.timestamp, self.velocity_list, self.angular_position_list)
            )

        self.velocity_list.clear()
        self.angular_position_list.clear()
        self.timestamp.clear()

    async def acquire_data(self):
        logger.info("Acquiring data during rotation task started")
        while True:
            self.timestamp.append(time.time())
            self.velocity_list.append(self.get_actual_velocity())
            self.angular_position_list.append(self.get_angular_position())
            await asyncio.sleep(1e-6)

    def connect(self) -> None:
        """
        Connects to the device.
        """
        self.my_interface = ConnectionManager(self.interface_args).connect()
        self.module = TMCM1021(self.my_interface)
        self.motor = self.module.motors[0]
        # to prevent the motor from moving at startup of application
        self.motor.stop()
        self.motor.actual_position = 0

    async def health_check(self) -> bool:
        try:
            self.motor.actual_position
            return True
        except Exception as e:
            logger.error("Error during health check: %s", e)
            return False

    def close(self) -> None:
        """
        Closes the connection to the device.
        """
        self.my_interface.close()

    def initialize_motor_settings(self) -> None:
        """
        Initializes the motor settings.
        """
        self.settings_handler.read_settings()
        print(self.settings_handler.settings)

        # preparing drive settings, curent values betweeen 0 and 255 (with some steps between, see docs)
        self.motor.drive_settings.max_current = int(
            self.settings_handler.settings["max_current"]
        )
        self.motor.drive_settings.standby_current = int(
            self.settings_handler.settings["standby_current"]
        )
        self.motor.drive_settings.boost_current = int(
            self.settings_handler.settings["boost_current"]
        )
        self.motor.drive_settings.microstep_resolution = (
            self.motor.ENUM.MicrostepResolution256Microsteps
        )

        self.set_acceleration(self.settings_handler.settings["max_acceleration"])
        self.set_max_velocity(self.settings_handler.settings["max_velocity"])

        logger.info(
            "Chopper wheel initialized with settings: %s", self.motor.drive_settings
        )

    async def rotate_demo(self) -> None:
        """
        Performs a rotation demo.
        """
        logger.info("Rotating...")
        self.motor.rotate(self.direction_modifier * self.motor.linear_ramp.max_velocity)
        await asyncio.sleep(2)
        logger.info("Stopping...")
        self.motor.stop()
        await asyncio.sleep(self.wait_time_after_rotation)
        logger.info("Actual position: %s", self.motor.actual_position)

    async def one_rotation(self) -> None:
        """
        Rotates the motor by one rotation.
        """
        self.motor.move_by(-self.steps_per_rotation)
        await asyncio.sleep(self.wait_time_after_rotation)

    async def one_flash_please(self) -> None:
        """
        Creates flash beam.
        """
        if not self.are_we_home_yet():
            logger.warning("Motor is not at home position, abort flash")
            return

        self.rotate_by_angle(360 + self.free_rot_angle)
        await self.wait_for_rotation()
        prev_accel = self.motor.linear_ramp.max_acceleration
        self.set_acceleration(2)
        self.rotate_by_angle(-self.free_rot_angle)
        await self.wait_for_rotation()

        if not self.are_we_home_yet():
            logger.warning("Caution! Motor has not reached home position after flash!")
        else:
            logger.info("Flash beam created")
            self.motor.stop()
            self.motor.actual_position = 0

        await asyncio.sleep(self.wait_time_after_rotation)

        self.motor.linear_ramp.max_acceleration = prev_accel

    async def wait_for_rotation(self) -> None:
        """
        Waits for the motor to stop rotating.
        """
        while not self.motor.get_position_reached():
            await asyncio.sleep(0.5)

    async def find_home(self) -> None:
        """
        Reinitialize the motor position to zero.
        """
        logger.info("start finding home ...")
        prev_curr = self.motor.drive_settings.max_current
        prev_accel = self.motor.linear_ramp.max_acceleration
        self.motor.drive_settings.max_current = 600
        self.motor.linear_ramp.max_acceleration = 25600

        homing_speed = 0.1  # rps
        speed = -int(homing_speed * self.steps_per_rotation)

        zero_reached = False
        self.motor.rotate(speed)
        await asyncio.sleep(0.1)  # ensure motor has moved past sensor

        while not zero_reached:
            if self.are_we_home_yet():
                self.motor.stop()
                zero_reached = True
                sign_of_speed = 1 if speed > 0 else -1
                move_back = int(
                    -sign_of_speed * 400
                )  # move back parameter (fine tuned)
                self.motor.actual_position = 0
                self.motor.move_to(move_back)
                self.motor.actual_position = 0
            await asyncio.sleep(0.001)

        await asyncio.sleep(0.5)
        self.motor.drive_settings.max_current = prev_curr
        self.motor.linear_ramp.max_acceleration = prev_accel

        if not self.are_we_home_yet():
            logger.warning("Failed to find home position")
        else:
            logger.info("Home position found")

    def are_we_home_yet(self) -> bool:
        """
        Check if the motor is at home position.
        """
        return self.module.get_digital_input(1) == 0

    def rotate_by_steps(self, steps: int) -> None:
        """
        Rotates the motor by the specified number of steps.

        Args:
            steps: The number of steps to rotate the motor.
        """
        self.motor.move_by(self.direction_modifier * steps)

    def rotate_by_angle(self, angle: float) -> None:
        """
        Rotates the motor by the specified angle.

        Args:
            angle: The angle to rotate the motor in degrees.
        """
        self.motor.move_by(self.direction_modifier * self._angle_to_steps(angle))

    def _angle_to_steps(self, angle: float) -> int:
        return int(angle * self.steps_per_rotation / 360)

    def get_position(self) -> float:
        """
        Gets the current position of the motor.

        Returns:
            The current position of the motor.
        """
        return self.direction_modifier * self.motor.actual_position

    def get_angular_position_from_zero(self) -> float:
        """
        Gets the angular position of the motor from zero.

        Returns:
            The angular position of the motor from zero in degrees.
        """
        pos = self.motor.actual_position / self.steps_per_rotation
        pos = pos - int(pos)
        return self.direction_modifier * pos * 360

    def get_angular_position(self) -> float:
        """
        Gets the angular position of the motor.

        Returns:
            The angular position of the motor in degrees.
        """
        pos = self.motor.actual_position / self.steps_per_rotation
        return self.direction_modifier * pos * 360

    def set_max_velocity(self, velocity: float) -> None:
        """
        Sets the maximum velocity of the motor.

        Args:
            velocity: The maximum velocity of the motor in rps.
        """
        self.motor.linear_ramp.max_velocity = int(velocity * self.steps_per_rotation)

    def get_max_velocity(self) -> float:
        """
        Gets the maximum velocity of the motor.

        Returns:
            The maximum velocity of the motor in rps.
        """
        return self.motor.linear_ramp.max_velocity / self.steps_per_rotation

    def set_acceleration(self, acceleration: float) -> None:
        """
        Sets the acceleration of the motor.

        Args:
            acceleration: The acceleration of the motor in rps squared.
        """
        self.motor.linear_ramp.max_acceleration = int(
            acceleration * self.steps_per_rotation
        )

    def get_max_acceleration(self) -> float:
        """
        Gets the maximum acceleration of the motor.

        Returns:
            The maximum acceleration of the acceleration in rps squared.
        """
        return self.motor.linear_ramp.max_acceleration / self.steps_per_rotation

    def get_actual_velocity(self) -> float:
        """
        Gets the actual velocity of the motor.

        Returns:
            The actual velocity of the motor in rps.
        """
        return (
            self.direction_modifier
            * self.motor.actual_velocity
            / self.steps_per_rotation
        )
