#!/usr/bin/env python3

import logging
from pathlib import Path

import numpy as np  # type: ignore
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
import asyncio
from nicegui import events, ui, app
from util import ComponentBase
from datetime import datetime
import csv

from controllers.stage import ArcusPerformaxDMXJSAStage
from util.settings_handler import SettingsHandler
from util.data_file_handler import DataFileHandler
from static.global_ui_props import *

logger = logging.getLogger()
work_dir = Path(__file__).parent


class StagesComponent(ComponentBase):
    def __init__(
        self,
        datafile_handler: DataFileHandler,
        settings_handler: SettingsHandler,
        stage_x: ArcusPerformaxDMXJSAStage,
        stage_y: ArcusPerformaxDMXJSAStage,
    ):
        super().__init__(None, datafile_handler, settings_handler)  # type: ignore

        self.stage_x = stage_x
        self.stage_y = stage_y

        self.joy_x = 0.0
        self.joy_y = 0.0
        self.using_joystick = False
        self.joystick_max_movement_speed = 3  # mm/s
        self.move_task: asyncio.Task = None  # type: ignore

        self.HALF_STAGE_WIDTH = 150  # mm

        self.joystick: ui.joystick

        self.plot_plotly = px.scatter(
            x=[0],
            y=[0],
        ).update_layout(
            margin=dict(l=2, r=2, b=2, t=2, pad=2),
            dragmode="zoom",
            xaxis_range=[-300, 300],
            yaxis_range=[-300, 300],
            xaxis_title="x [mm]",
            yaxis_title="y [mm]",
            width=600,
            height=600,
        )
        self.plot_plotly.update_traces(marker=dict(symbol="x", size=15))

        ui.timer(0.1, self.update_plot)
        self.x_prev = None
        self.y_prev = None

        # log position every 5 seconds
        ui.timer(5, self.log_position)

    def update_plot(self):
        
        if self.stage_x.position is None or self.stage_y.position is None:
            return
        
        x = -self.stage_x.position
        y = -self.stage_y.position

        if self.x_prev == x and self.y_prev == y:
            return

        self.x_prev = x
        self.y_prev = y

        self.plot_plotly.data = [self.plot_plotly.data[0]]
        self.plot_plotly.add_trace(
            go.Scatter(
                x=[
                    x - self.HALF_STAGE_WIDTH,
                    x + self.HALF_STAGE_WIDTH,

                    x + self.HALF_STAGE_WIDTH,
                    x - self.HALF_STAGE_WIDTH,
                ],
                y=[
                    y - self.HALF_STAGE_WIDTH,
                    y - self.HALF_STAGE_WIDTH,

                    y + self.HALF_STAGE_WIDTH,
                    y + self.HALF_STAGE_WIDTH,
                ],
                fill="toself",
                line=dict(color="rgba(0,0,0,0.01)"),
                showlegend=False,
            )
        )
        self.plot_nicegui.update()

    @ui.refreshable
    def plot(self):
        self.plot_nicegui = ui.plotly(self.plot_plotly)

    def create_ui(self):

        async def move_stages():
            sleep_time = 0.5  # seconds
            distance_at_max_speed = self.joystick_max_movement_speed * sleep_time
            while self.using_joystick and self.fully_connected():
                self.stage_x.move_by(-self.joy_x * distance_at_max_speed)
                self.stage_y.move_by(-self.joy_y * distance_at_max_speed)
                logger.info(
                    f"Moving stages by x: {(self.joy_x * distance_at_max_speed):.2f}, y: {(self.joy_y * distance_at_max_speed):.2f}"
                )
                await asyncio.sleep(sleep_time)

        def on_start(e: events.JoystickEventArguments):
            self.using_joystick = True
            self.move_task = asyncio.create_task(move_stages())

        def on_move(e: events.JoystickEventArguments):
            if e.x is None or e.y is None:
                self.joy_x = 0
                self.joy_y = 0
            else:
                self.joy_x = e.x
                self.joy_y = e.y

        def on_end(e: events.JoystickEventArguments):
            self.using_joystick = False

        with ui.splitter(value=40).classes("w-full") as splitter:
            with splitter.before:
                with ui.element().classes("flex m-1 p-4 w-full justify-center"):
                    with ui.card().classes("w-full mb-2"):
                        app.storage.general.get("setting_stages_absolute_movement_mode", True)
                        ui.switch(value=False, text="Absolute Movement Mode").bind_value(app.storage.general, "setting_stages_absolute_movement_mode")

                    with ui.card().classes("w-full mb-2"):
                        ui.label("Stage X").classes("center justify-self-center")
                        self.stage_ui(self.stage_x, "x")

                    with ui.card().classes("w-full mb-2"):
                        ui.label("Stage Y").classes("center justify-self-center")
                        self.stage_ui(self.stage_y, "y")
                
                    with ui.card().classes("w-full mb-2"):
                        with ui.expansion("Position Log File Settings", icon="analytics", value=False).classes( "w-full justify-items-center"):
                            self.file_handler.alternative_filename_ui()
                            with ui.grid(columns=3, rows=1).classes("w-full gap-2 justify-items-stretch"):
                                self.file_handler.download_file_button_ui()
                                self.file_handler.save_download_clear_button_ui()
                                self.file_handler.delete_file_button_ui()
                            self.file_handler.create_ui()

            with splitter.after:
                with ui.element().classes("flex w-full justify-center items-center"):
                    self.plot()

                    with ui.element().classes(""):
                        ui.label("JoyStick:")
                        self.joystick = ui.joystick(
                            color="blue",
                            on_move=on_move,
                            on_end=on_end,
                            on_start=on_start,
                            mode="static",
                        ).classes("bg-white-400 dark:bg-black-400")
                        ui.query(f"#c{self.joystick.id} > div").style(
                            "background-color:unset;"
                        )

    def stage_ui(self, stage: ArcusPerformaxDMXJSAStage, axis: str):
        with ui.grid(columns=2).classes("m-1 w-full justify-center"):
            ui.label('Axis status:')
            ui.label().bind_text_from(stage, "axis_status", backward=str)

            ui.label("Axis limit errors:")
            ui.label().bind_text_from(stage, "current_limit_errors", backward=str)

            ui.label("Moving:")
            ui.label().bind_text_from(stage, "moving", backward=str)

            ui.label("Position [mm]:")
            ui.label().bind_text_from(stage, "position", backward=str)

            move_by = (
                ui.number(value=0, label=f"{axis} - Move by [mm]")
                .bind_visibility_from(app.storage.general, "setting_stages_absolute_movement_mode", lambda x: not x)
                .props(props_input)
            )
            ui.button(
                f"{axis} - Move by", on_click=lambda: stage.move_by(move_by.value)
            ).classes("p-0 m-3").props(
                "no-caps unelevated rounded"
            ).bind_visibility_from(
                app.storage.general, "setting_stages_absolute_movement_mode", lambda x: not x
            )

            move_to = (
                ui.number(value=0, label=f"{axis} - Move to [mm]")
                .bind_visibility_from(app.storage.general, "setting_stages_absolute_movement_mode", lambda x: x)
                .props(props_input)
            )
            ui.button(
                f"{axis} - Move to", on_click=lambda: stage.move_to(move_to.value)
            ).classes("p-0 m-3").props(props_button).bind_visibility_from(
                app.storage.general, "setting_stages_absolute_movement_mode", lambda x: x
            )

            with ui.dialog() as dialog, ui.card():
                ui.label(
                    f'Are you sure you want to set the current position as the new 0 position for axis "{axis}" ?'
                )
                with ui.row().classes("w-full justify-center items-center"):

                    def confirm_action():
                        stage.set_zero()
                        dialog.close()

                    ui.button("Yes, zero it!", on_click=confirm_action).props(
                        props_button
                    )
                    ui.button("No, I was too fast!", on_click=dialog.close).props(
                        props_button
                    )

            ui.button(
                f"{axis} - Set current position as zero",
                on_click=dialog.open,
                color="grey",
            ).classes("col-span-2 p-0").props(props_button)

    def fully_connected(self):
        return self.stage_x.connected and self.stage_y.connected

    def set_dark_mode(self, value: bool):
        self.dark_mode = value
        try:
            self.plot_plotly.update_layout(
                go.Layout(template="plotly_dark" if value else "seaborn")
            )
            self.plot_nicegui.update()

        except AttributeError as e:
            pass

    def log_position(self):
        if self.fully_connected():
            filename = self.file_handler.full_filename
            # check positions of last log
            x = 0
            y = 0
            with open(filename, "r", newline="", encoding="utf-8") as f:
                lines = f.readlines()
                if len(lines) > 1:
                    last_line = lines[-1]
                    _, x, y = last_line.split(",")
                    x = float(x)
                    y = float(y)

            # compare with current position
            if x != self.stage_x.position or y != self.stage_y.position:
                with open(filename, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([datetime.now(), self.stage_x.position, self.stage_y.position])

    def main_page_ui(self):
        pass
