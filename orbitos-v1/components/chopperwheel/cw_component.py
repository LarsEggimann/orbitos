#!/usr/bin/env python3

import csv
import logging
from multiprocessing.connection import Connection
from pathlib import Path
import asyncio
from datetime import datetime
import numpy as np
from static.global_ui_props import *
import plotly.graph_objects as go  # type: ignore
from components import param_settings_row
from nicegui import ui, app
from util.component_base import ComponentBase
from util.data_file_handler import DataFileHandler
from util.settings_handler import SettingsHandler

logger = logging.getLogger()
main_working_directory = Path(__file__).parent.parent

def map_to_datetime(timestamp: str) -> datetime:
    return datetime.fromtimestamp(float(timestamp))

class CWComponent(ComponentBase):
    """UI Component for the Chopper Wheel control panel."""

    def __init__(
        self,
        pipe: Connection,
        file_handler: DataFileHandler,
        settings_handler: SettingsHandler,
    ):
        super().__init__(pipe, file_handler, settings_handler)

        self.name = "Chopper Wheel"

        self.redraw_plot_wait_time = 0.2
        self.max_plot_angle_range_setting_enabled = False
        self.max_plot_angle_range = 3 * 360

        self.velocity_warning = 3
        self.velocity_max = 4
        self.acceleration_warning = 8
        self.acceleration_max = 10

        self.position_label: ui.label
        self.home_position_label: ui.label

        self.one_flash_please_delay = 0.2

        self.velocity_list: list[float] = []
        self.angular_position_list: list[float] = []
        self.timestamp_list: list[datetime] = []

        self.angle_velocity_plot = go.Figure(
            go.Scattergl(
                x=[0],
                y=[0],
                mode="lines",
            )
        ).update_layout(
            margin=dict(l=2, r=2, b=2, t=2, pad=2),
            dragmode="zoom",
            xaxis_title="Angular Position [°]",
            yaxis_title="Velocity [rps]",
        )

        self.time_velocity_plot = go.Figure(
            go.Scattergl(
                x=[0],
                y=[0],
                mode="lines",
            )
        ).update_layout(
            margin=dict(l=2, r=2, b=2, t=2, pad=2),
            dragmode="zoom",
            xaxis_title="Time [datetime]",
            yaxis_title="Velocity [rps]",
        )

        self.timestamp_last_flash: datetime = datetime.now()

    @ui.refreshable
    def plot(self):
        with ui.grid(columns=2, rows=1).classes("w-full justify-center"):
            self.angle_velocity_nicegui = ui.plotly(self.angle_velocity_plot).classes(replace="w-full h-96")
            self.time_velocitiy_nicegui = ui.plotly(self.time_velocity_plot).classes(replace="w-full h-96")

    @ui.refreshable
    def create_ui(self):

        resize = (
            ui.button()
            .on("resize", self.plot.refresh, throttle=0.05) # pylint: disable=no-member
            .classes("hidden")  # pylint: disable=no-member
        ) 
        ui.add_head_html(
            f"""
        <script>
        function emitResizeEvent() {{
            content = document.querySelector('.nicegui-content');
            getElement({resize.id}).$emit('resize', content.offsetWidth);
        }}
        window.onload = emitResizeEvent;
        window.onresize = emitResizeEvent;
        </script>
        """
        )

        self.settings_handler.read_settings()
        self.plot()
        self.update_plot_timer = ui.timer(0.2, self.update_plots)

        with ui.card().classes("w-full mb-2"):
            with ui.grid(columns=3, rows=1).classes(
                "w-full gap-2 justify-items-stretch"
            ):
                ui.button(
                    "Find home", on_click=lambda: self.pipe.send("find_home")
                ).props(props_button)

                ui.button(
                    "One Flash Please",
                    on_click=self.one_flash_please,
                ).props(props_button)

                def on_change_delay(e):
                    self.one_flash_please_delay = e.value
                    app.storage.general["one_flash_please_delay"] = e.value
                    logger.info("one_flash_please_delay: %s", self.one_flash_please_delay)

                self.one_flash_please_delay = app.storage.general.get("one_flash_please_delay", 0.2)
                ui.number("One Flash Please Delay [s]", value=self.one_flash_please_delay, on_change=on_change_delay)

        with ui.card().classes("w-full mb-2"):
            with ui.grid(columns=3).classes(
                "w-full gap-2 justify-items-left items-center"
            ):
                param_settings_row.create_param_settings_row(
                    label_text="Max Velocity [rps]",
                    number_input_value=self.settings_handler.settings["max_velocity"],
                    setting_on_change=lambda value: self.settings_handler.change_setting(
                        "max_velocity", float(value)
                    ),
                    validation_dict={
                        "Be careful with this!": lambda value: int(value)
                        < self.velocity_warning
                    },
                    slider_limits=(0, self.velocity_max),
                )

                param_settings_row.create_param_settings_row(
                    label_text="Max Acceleration [rps/s]",
                    number_input_value=self.settings_handler.settings[
                        "max_acceleration"
                    ],
                    setting_on_change=lambda value: self.settings_handler.change_setting(
                        "max_acceleration", float(value)
                    ),
                    validation_dict={
                        "Be careful with this!": lambda value: int(value)
                        < self.acceleration_warning
                    },
                    slider_limits=(0, self.acceleration_max),
                )

                param_settings_row.create_param_settings_row(
                    label_text="Max Motor Current",
                    number_input_value=self.settings_handler.settings["max_current"],
                    setting_on_change=lambda value: self.settings_handler.change_setting(
                        "max_current", int(value)
                    ),
                    validation_dict={
                        "Not Allowed Value, will not be set!": lambda value: int(value)
                        < 256
                    },
                    slider_limits=(0, 255),
                )

                param_settings_row.create_param_settings_row(
                    label_text="Plot Refresh Wait Time [s]",
                    number_input_value=self.redraw_plot_wait_time,
                    setting_on_change=lambda e: setattr(
                        self, "redraw_plot_wait_time", e.value
                    ),
                    slider_limits=(0.01, 1),
                )

        with ui.card().classes("w-full mb-2"):
            self.file_handler.alternative_filename_ui()
            with ui.grid(columns=3, rows=1).classes(
                "w-full gap-2 justify-items-stretch"
            ):
                self.file_handler.download_file_button_ui()
                self.file_handler.save_download_clear_button_ui()
                self.file_handler.delete_file_button_ui()

        with ui.card().classes("w-full mb-2"):
            self.file_handler.create_ui()

        with ui.expansion("Testing", icon="bug_report").classes(add="w-full"):
            with ui.grid(columns=4, rows=5).classes(
                "w-full gap-2 justify-items-left items-center"
            ):
                ui.button(
                    "Test Get Settings", on_click=lambda: self.pipe.send("get_settings")
                ).props(props_button)
                ui.button(
                    "rotate demo",
                    on_click=lambda: self.pipe.send("rotate_demo"),
                ).props(props_button)
                ui.button(
                    "one rotation",
                    on_click=lambda: self.pipe.send("one_rotation"),
                ).props(props_button)

    def main_page_ui(self):
        ui.label("Chopper Wheel Main Page UI")
        ui.button("Find home", on_click=lambda: self.pipe.send("find_home")).props(
            props_button
        )

    async def one_flash_please(self):
        await asyncio.sleep(self.one_flash_please_delay)
        logger.info(f"starting one flash please for {self.name}")
        self.timestamp_last_flash = datetime.now()
        self.pipe.send("one_flash_please")
        logger.info(f"finished one flash please for {self.name} sent")

    def reset_plots(self):
        self.velocity_list.clear()
        self.angular_position_list.clear()
        self.timestamp_list.clear()

        self.angle_velocity_plot.data = [self.angle_velocity_plot.data[0]]
        self.time_velocity_plot.data = [self.time_velocity_plot.data[0]]

        self.angle_velocity_plot.update_traces(x=[0], y=[0])
        self.time_velocity_plot.update_traces(x=[0], y=[0])

        self.angle_velocity_plot.layout.shapes = []
        self.time_velocity_plot.layout.shapes = []

        self.angle_velocity_nicegui.update()
        self.time_velocitiy_nicegui.update()

    def read_data_from_file(self):
        with open(
            self.file_handler.full_filename, "r", newline="", encoding="utf-8"
        ) as f:
            reader = csv.reader(f)
            next(reader)
            data = list(zip(*reader))

        if data:
            timestamps = list(map(map_to_datetime, data[0]))
            velocities = list(map(float, data[1]))
            angular_positions = list(map(float, data[2]))
        else:
            timestamps, velocities, angular_positions = [], [], []

        return timestamps, velocities, angular_positions

    def update_plots(self):

        # Check if the file has been modified
        if self.file_handler.new_data_or_new_file():

            self.angle_velocity_plot.data = [self.angle_velocity_plot.data[0]]
            self.time_velocity_plot.data = [self.time_velocity_plot.data[0]]

            self.timestamp_list, self.velocity_list, self.angular_position_list = self.read_data_from_file()

        
            index_of_new_datapoint = np.where(np.array(self.timestamp_list) > self.timestamp_last_flash)[0]
            if index_of_new_datapoint.size > 0:
                index_of_new_datapoint = index_of_new_datapoint[0]
            else:
                index_of_new_datapoint = len(self.timestamp_list)

            old_velocity_list = self.velocity_list[:index_of_new_datapoint]
            new_velocity_list = self.velocity_list[index_of_new_datapoint:]
            old_angular_position_list = self.angular_position_list[:index_of_new_datapoint]
            new_angular_position_list = self.angular_position_list[index_of_new_datapoint:]

            self.angle_velocity_plot.update_traces(
                x=new_angular_position_list,
                y=new_velocity_list,
                name="Current Flash"
            )

            self.angle_velocity_plot.add_trace(
                go.Scatter(
                    x=old_angular_position_list,
                    y=old_velocity_list,
                    name="Previous Flash's"
                )
            )

            if len(self.angular_position_list) > 0:
                beta = 70
                y_max = max(self.velocity_list)
                self.angle_velocity_plot.add_trace(
                    go.Scatter(
                        x=[
                            360,
                            360,
                            360 - beta,
                            360 - beta,
                        ],
                        y=[-y_max, y_max, y_max, -y_max],
                        fill="toself",
                        line=dict(color="rgba(0,0,0,0)"),
                        text="Proton Beam",
                        name="Proton Beam",
                    )
                )

            self.time_velocity_plot.update_traces(
                x=self.timestamp_list,
                y=self.velocity_list,
            )

            self.angle_velocity_nicegui.update_figure(self.angle_velocity_plot)
            self.time_velocitiy_nicegui.update_figure(self.time_velocity_plot)

    def set_dark_mode(self, value: bool):
        self.dark_mode = value
        try:
            self.angle_velocity_plot.update_layout(
                go.Layout(template="plotly_dark" if value else "seaborn")
            )
            self.angle_velocity_nicegui.update()
            self.time_velocity_plot.update_layout(
                go.Layout(template="plotly_dark" if value else "seaborn")
            )
            self.time_velocitiy_nicegui.update()
        except AttributeError:
            pass
