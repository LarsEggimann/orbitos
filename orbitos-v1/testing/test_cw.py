#!/usr/bin/env python3
import logging
from pathlib import Path
from nicegui import app, ui
import asyncio
import logging
from pytrinamic.connections import ConnectionManager  # type: ignore
from pytrinamic.modules import TMCM1021  # type: ignore


logger = logging.getLogger()
working_directory = Path(__file__).parent

class Value:
    value = None



@ui.page("/main")
async def main():
    ui.label("Hello, world!")

    cw = ChopperWheel()

    ui.button("Find Home", on_click=cw.find_home)
    ui.button("One Rotation", on_click=cw.one_rotation)
    ui.button("Rotate by 10000 steps", on_click=lambda: cw.rotate_by_steps(10000))

    are_we_home_yet = Value()
    pos = Value()
    digital_inputs = Value()

    ui.label().bind_text_from(are_we_home_yet, "value", backward=lambda x: f"Are we home yet: {x}")
    ui.label().bind_text_from(pos, "value", backward=lambda x: f"Position: {x}")
    ui.label().bind_text_from(digital_inputs, "value", backward=lambda x: f"Digital Inputs: {x}")

    def set_are_we_home_yet():
        are_we_home_yet.value = cw.are_we_home_yet()
    ui.timer(0.1, set_are_we_home_yet, active=True)

    def set_pos():
        pos.value = cw.get_position()
    ui.timer(0.1, set_pos, active=True)

    def set_digital_inputs():
        digital_inputs.value = cw.get_digital_inputs()
    ui.timer(0.1, set_digital_inputs, active=True)


if __name__ in {"__main__", "__mp_main__"}:

    def on_start():
        urls = " http://localhost:50050, http://192.168.113.7:50050"
        print(f"Test CW ready on: {urls}")
    
    app.on_startup(on_start)
    ui.navigate.to("/main")

    ui.run(
        reload=True,
        show=True,
        on_air=None,
        binding_refresh_interval=0.1,
        host="0.0.0.0",
        title="CW TEst",
        favicon=str(working_directory / "static" / "icon.ico"),
        port=50050,
        show_welcome_message=False,
        storage_secret="flash-control-panel",
    )

class ChopperWheel:
    def __init__(self) -> None:

        self.address = "COM10"

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
            self.motor.drive_settings.max_current = 1000
            self.motor.drive_settings.standby_current = 0
            self.motor.drive_settings.boost_current = 0
            self.motor.drive_settings.microstep_resolution = (
            self.motor.ENUM.MicrostepResolution256Microsteps
            )
        except Exception as e:
            logger.error("Could not connect to the device.")
            logger.error(e)


    def connect(self) -> None:
        self.my_interface = ConnectionManager(self.interface_args).connect()
        self.module = TMCM1021(self.my_interface)
        self.motor = self.module.motors[0]
        # to prevent the motor from moving at startup of application
        self.motor.stop()
        self.motor.actual_position = 0


    async def one_rotation(self) -> None:
        self.motor.move_by(-self.steps_per_rotation)
        await asyncio.sleep(0.1)


    async def find_home(self) -> None:
        """
        Reinitialize the motor position to zero.
        """
        print("start finding home ...")
        prev_curr = self.motor.drive_settings.max_current
        prev_accel = self.motor.linear_ramp.max_acceleration
        self.motor.drive_settings.max_current = 600
        self.motor.linear_ramp.max_acceleration = 25600

        homing_speed = 0.1  # rps
        speed = -int(homing_speed * self.steps_per_rotation)

        zero_reached = False
        self.motor.rotate(speed)
        await asyncio.sleep(1)  # ensure motor has moved past sensor

        i = 0

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
            i += 1
            if i % 20 == 0:
                print(f"still finding home ... current position:{self.get_position()}")
                print(f"Digital Inputs: {self.get_digital_inputs()}")

        await asyncio.sleep(0.5)
        self.motor.drive_settings.max_current = prev_curr
        self.motor.linear_ramp.max_acceleration = prev_accel

        if not self.are_we_home_yet():
            logger.warning("Failed to find home position")
        else:
            print("Home position found")

    def are_we_home_yet(self) -> bool:
        res = self.module.get_digital_input(1) == 0
        return res
    
    def get_digital_inputs(self) -> str:
        return f"{self.module.get_digital_input(0)}{self.module.get_digital_input(1)}{self.module.get_digital_input(2)}{self.module.get_digital_input(3)}"

    def rotate_by_steps(self, steps: int) -> None:
        self.motor.move_by(self.direction_modifier * steps)

    def rotate_by_angle(self, angle: float) -> None:
        self.motor.move_by(self.direction_modifier * self._angle_to_steps(angle))

    def _angle_to_steps(self, angle: float) -> int:
        return int(angle * self.steps_per_rotation / 360)

    def get_position(self) -> float:
        return self.direction_modifier * self.motor.actual_position
