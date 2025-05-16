#!/usr/bin/env python3

import csv
import logging
from multiprocessing.connection import Connection
from pathlib import Path
import os
import asyncio

import time
from datetime import datetime, timedelta
import numpy as np  # type: ignore
import plotly.graph_objects as go  # type: ignore
from nicegui import ui, app
from util import ComponentBase
from util.data_file_handler import DataFileHandler
from util.settings_handler import SettingsHandler
from static.global_ui_props import *



logger = logging.getLogger()
main_working_directory = Path(__file__).parent.parent


def nA_to_A(nA: float) -> float:
    return nA * 1e-9


def A_to_nA(A: float) -> float:
    return A * 1e9


def cast_to_float(value: str) -> float:
    return float(value)

def map_to_datetime(x):
    return datetime.fromtimestamp(float(x))

def map_to_timestamp(x):
    return x.timestamp()


class ICComponent(ComponentBase):
    def __init__(
        self,
        pipe: Connection,
        file_handler: DataFileHandler,
        settings_handler: SettingsHandler,
        name="em"
    ):
        super().__init__(pipe, file_handler, settings_handler)

        self.name = name

        self.time_list: list[datetime] = []
        self.current_list: list[float] = []
        self.integrated_charge: float = 0
        self.dose_conversion_param = None

        self.custom_value: float = 0
        self.calculated_dose_from_custom_value: float = 0

        self.is_there_new_data = False
        self.update_plot_interval = 0.3

        self.xaxis_range_control_enabled = False
        self.xaxis_range_scale_factor = 60 # seconds
        self.xaxis_range_slider_value = 1 # [0,1]
        self.xaxis_range = timedelta(seconds=self.xaxis_range_scale_factor * self.xaxis_range_slider_value)

        self.disable_plot_update = False

        self.plot_plotly = go.Figure(
            go.Scattergl(
                x=[0],
                y=[0],
                mode="lines",
            )
        ).update_layout(
            margin=dict(l=2, r=2, b=2, t=2, pad=2),
            dragmode="zoom",
            xaxis_title="Time [datetime]",
            yaxis_title="Current [A]",
        )

    def show_current_data_in_new_window(self):
        fig = go.Figure()
        copy_filename = self.file_handler.copy_current_data_to_new_temp_file()
        fig.add_trace(
            go.Scattergl(
                x=self.time_list,
                y=self.current_list,
                mode="lines",
                name="Current [A]",
            )
        )
        fig.update_layout(
            title="Electrometer Data",
            xaxis_title="Time [s]",
            yaxis_title="Current [A]",
            template="plotly_dark" if self.dark_mode else "seaborn",
        )

        @ui.page("/em/{file_name}")
        def page():
            ui.plotly(fig).classes("w-full h-100")
            ui.button(
                "Download CSV", on_click=lambda: ui.download(copy_filename)
            ).props(props_button)

        ui.navigate.to(f"/em/{os.path.basename(copy_filename)}", new_tab=True)

    def close_connection_to_keysight_em(self):
        self.pipe.send("exit")

    def read_data_from_file(self):
        data = []
        times = []
        currents = []
        
        # Open the file and seek to the last position
        with open(self.file_handler.full_filename, "r", newline="", encoding="utf-8") as f:
            f.seek(self.file_handler.last_position_read)  # Go to the last read position
            
            # Use csv reader to process only new lines
            reader = csv.reader(f)
            if self.file_handler.last_position_read == 0:  # Skip header only when first time
                next(reader)
                # clear the data lists
                self.time_list.clear()
                self.current_list.clear()
            
            # Append new lines from file
            new_data = list(reader)
            if new_data:
                data.extend(new_data)

            # Update last position for next read
            self.file_handler.last_position_read = f.tell()

        if data:
            # Process data into lists (transpose)
            data = list(zip(*data))
            times = list(map(map_to_datetime, data[0]))
            currents = list(map(float, data[1]))
        else:
            times, currents = [], []
        
        self.time_list.extend(times)
        self.current_list.extend(currents)


    async def receive_data(self):
        if self.file_handler.new_data_or_new_file():
            await self.do_receive_data()

    async def do_receive_data(self):
        self.read_data_from_file()

        if self.xaxis_range_control_enabled:
            self.calc_xaxis_range()

        self.is_there_new_data = True        

    async def update_plot(self):
        if self.is_there_new_data and not self.disable_plot_update:
            await self.do_update_plot()
            
    
    async def do_update_plot(self):
        self.plot_plotly.data = [self.plot_plotly.data[0]]

        self.integrated_charge = np.trapz(self.current_list, list(map(map_to_timestamp, self.time_list)))

        self.plot_plotly.update_traces(
            x=self.time_list,
            y=self.current_list,
        )

        self.is_there_new_data = False
        self.plot_nicegui.update()
    
    def calc_xaxis_range(self):
       
        times = np.array(self.time_list)
        currents = np.array(self.current_list)
        if times.size == 0 or currents.size == 0 or self.xaxis_range_scale_factor is None:
            return
        
        self.xaxis_range = timedelta(seconds=self.xaxis_range_scale_factor * self.xaxis_range_slider_value)
        
        start_time = times[-1] - self.xaxis_range
        
        condition = times >= start_time

        times = times[condition]
        currents = currents[condition]

        self.time_list = times.tolist()
        self.current_list = currents.tolist()

    async def wait_for_trigger_based_measurement(self):
        n = ui.notification(timeout=None, close_button=True, position="top")

        measurement_time = self.settings_handler.settings["trigger_time_interval"] * self.settings_handler.settings["trigger_count"] + 1
        start_time = time.time()

        while time.time() - start_time < measurement_time:
            n.spinner = True
            n.message = f"Trigger based measurement: {time.time() - start_time:.2f} / {measurement_time:.2f} seconds"
            await asyncio.sleep(0.2)
        
        n.message = "Finished Measurement"
        n.type = "positive"
        n.spinner = False
        await asyncio.sleep(3)
        n.dismiss()

    def trigger_based_measurement(self):
        self.pipe.send("do_trigger_based_measurement")
        ui.timer(0.1, self.wait_for_trigger_based_measurement, once=True)
        

    async def one_flash_please(self):
        logger.info(f"starting one flash please for {self.name}")
        self.trigger_based_measurement()
        logger.info(f"finished one flash please for {self.name}")


    @ui.refreshable
    def plot(self):

        self.plot_nicegui = ui.plotly(self.plot_plotly).classes("w-full h-96")

    @ui.refreshable
    def create_ui(self):
        resize = (
            ui.button()
            .on(
                "resize", lambda: self.plot.refresh, throttle=0.05 # pylint: disable=no-member
            )
            .classes("hidden")
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
        
        # reset last position in file to load all data fresh
        self.file_handler.last_position_read = 0
        self.time_list.clear()
        self.current_list.clear()

        self.settings_handler.read_settings()


        setting_continous_measurement = f"setting_continuous_measurement_{self.name}"
        app.storage.general.get(setting_continous_measurement, True)


        with ui.card().classes("w-full mb-2"):
            with ui.row(wrap=False).classes("w-full items-center justify-between p-1"):

                with ui.row(wrap=False).classes("w-full items-center"):
                    ui.label("Plot -")
                    ui.switch(text="Auto refresh", value=True).bind_value_to(self, "disable_plot_update", forward=lambda x: not x).tooltip("Toggle automatic plot update")

                async def do_the_updates():
                    self.file_handler.last_position_read = 0
                    self.xaxis_range_control_enabled = app.storage.general.get(setting_x_axis_range_control, False)
                    app.storage.general[setting_x_axis_range_scale_factor] = self.xaxis_range_scale_factor
                    await self.do_receive_data()
                    await self.do_update_plot()

                
                setting_x_axis_range_control = f"setting_x_axis_range_control_{self.name}"
                setting_x_axis_range_scale_factor = f"setting_x_axis_range_scale_factor_{self.name}"
                self.xaxis_range_control_enabled = app.storage.general.get(setting_x_axis_range_control, False)
                self.xaxis_range_scale_factor = app.storage.general.get(setting_x_axis_range_scale_factor, 60)

                ui.label("Control x-axis range: ")
                ui.switch(on_change=do_the_updates).bind_value(app.storage.general, setting_x_axis_range_control).tooltip("Toggle x-axis range control")
                ui.number(label='Scale factor in seconds', step=1, on_change=do_the_updates).bind_value(self, "xaxis_range_scale_factor").bind_enabled_from(app.storage.general, setting_x_axis_range_control, lambda x: x)
                ui.slider(min=0, max=1, step=0.01, value=1, on_change=do_the_updates).bind_value_to(self, "xaxis_range_slider_value").bind_enabled_from(app.storage.general, setting_x_axis_range_control, lambda x: x)
                ui.label().bind_text_from(self, "xaxis_range", backward=lambda x: f"X-axis range: {x.total_seconds():.2f}s")

        self.plot()
        self.recieve_data_timer = ui.timer(
            self.update_plot_interval, self.receive_data
        )
        self.update_plot_timer = ui.timer(
            self.update_plot_interval, self.update_plot
        )


        param_name = f"dose_conversion_param_{self.name}"
        self.dose_conversion_param = app.storage.general.get(param_name, 1)

        with ui.card().classes("w-full mb-2"):
            with ui.row(wrap=False).classes("w-full items-center justify-between p-1"):
                ui.label().bind_text_from(self, "integrated_charge", backward=lambda x: f"Integrated charge: {x:.5e} C")                

                with ui.row(wrap=False).classes("items-center"):
                    ui.label("Dose conversion factor [Gy/C]: ")
                    ui.number(value=self.dose_conversion_param).bind_value_to(app.storage.general, param_name)

                    def clac_dose(x):
                        if x is None or app.storage.general[param_name] is None:
                            return "?? Gy"
                        return f"{(x * app.storage.general[param_name]):.5e} Gy"
                    
                    ui.label().bind_text_from(self, "integrated_charge", backward=clac_dose)



        with ui.card().classes("w-full mb-2"):
            with ui.grid(columns=3).classes("w-full justify-items-stretch p-4"):
                ui.button(
                    "Trigger based measurement",
                    on_click=self.trigger_based_measurement,
                ).props(props_button).bind_enabled_from(
                    app.storage.general, setting_continous_measurement, lambda x: not x
                ).tooltip(
                    "Do a single trigger based measurement"
                )

                ui.button(
                    "Start continuous",
                    on_click=lambda: self.pipe.send("start_continuous_measurement"),
                ).props(props_button).bind_enabled_from(
                    app.storage.general, setting_continous_measurement
                ).tooltip(
                    "Start continuous measurement"
                )
                ui.button(
                    "Stop continuous",
                    on_click=lambda: self.pipe.send("stop_continuous_measurement"),
                ).props(props_button).tooltip("Stop continuous measurement")

        with ui.card().classes("w-full mb-2"):
            ui.label("Trigger settings")
            ui.separator()
            with ui.grid(columns=2).classes(
                "w-full gap-2 justify-items-left items-center"
            ):

                ui.label("Continuous measurement: ")
                ui.switch().bind_value(app.storage.general, setting_continous_measurement)

                ui.label("Trigger time interval: ")
                ui.number(
                    min=0.000001,
                    max=1,
                    step=0.01,
                    suffix="[s]",
                ).bind_value(
                    self.settings_handler.settings,
                    "trigger_time_interval",
                    backward=cast_to_float,
                ).on(
                    "update:model-value",
                    self.settings_handler.settings_changed,
                    throttle=1.0,
                ).bind_enabled_from(
                    app.storage.general, setting_continous_measurement, lambda x: not x
                ).props(
                    props_input
                )

                ui.label("Trigger count: ")
                ui.number(
                    min=1,
                    max=100000000,
                    step=10,
                ).bind_value(
                    self.settings_handler.settings,
                    "trigger_count",
                    backward=cast_to_float,
                ).on(
                    "update:model-value",
                    self.settings_handler.settings_changed,
                    throttle=1.0,
                ).bind_enabled_from(
                    app.storage.general, setting_continous_measurement, lambda x: not x
                ).props(
                    props_input
                )

                ui.label().bind_text_from(
                    self.settings_handler.settings,
                    "trigger_time_interval",
                    backward=lambda x: "Total time for measurement: "
                    + str(
                        self.settings_handler.settings["trigger_time_interval"]
                        * self.settings_handler.settings["trigger_count"]
                    ),
                ).bind_visibility_from(app.storage.general, setting_continous_measurement, lambda x: not x)


        current_range_auto = 0
        auto_current_range = f"setting_contiauto_current_rangenuous_measurement_{self.name}"
        app.storage.general.get(auto_current_range, True)

        with ui.card().classes("w-full mb-2"):
            ui.label("Range settings")
            ui.separator()
            with ui.grid(columns=2).classes(
                "w-full gap-2 justify-items-left items-center p-1"
            ):
                ui.label("Current range: ")
                current_range = ReactiveNumber(
                    float(self.settings_handler.settings["current_range"]) * 1e9
                )
                
                def get_auto_current_range_value():
                    value = self.settings_handler.settings["current_range_auto"]
                    if value in ["ON", True, 1, "True"]:
                        return True
                    return False
                auto_current_range = ReactiveNumber(get_auto_current_range_value())

                ui.number(min=0, step=0.0001, suffix="[nA]").bind_value(
                    current_range, "value"
                ).bind_enabled_from(auto_current_range, "value", lambda x: not x).on(
                    "update:model-value",
                    lambda: self.settings_handler.change_setting(
                        "current_range", current_range.get_value_in_Amp()
                    ),
                    throttle=1.0,
                ).props(
                    props_input
                )


                def change_auto_current_range(value):
                    if value in ["ON", True, 1, "True"]:
                        value = "ON"
                    else:
                        value = "OFF"
                    self.settings_handler.change_setting("current_range_auto", value)

                ui.label("Auto current range: ")
                ui.switch(
                    on_change=lambda x: change_auto_current_range(x.value)
                ).bind_value(auto_current_range, "value")

                ui.label("Auto current range upper limit: ")
                auto_upper_limit = ReactiveNumber(
                    float(
                        self.settings_handler.settings["current_range_auto_upper_limit"]
                    )
                    * 1e9
                )
                ui.number(min=0, step=0.0001, suffix="[nA]").bind_value(
                    auto_upper_limit, "value"
                ).bind_enabled_from(auto_current_range, "value").on(
                    "update:model-value",
                    lambda: self.settings_handler.change_setting(
                        "current_range_auto_upper_limit",
                        auto_upper_limit.get_value_in_Amp(),
                    ),
                    throttle=1.0,
                ).props(
                    props_input
                )

                ui.label("Auto current range lower limit: ")
                auto_lower_limit = ReactiveNumber(
                    float(
                        self.settings_handler.settings["current_range_auto_lower_limit"]
                    )
                    * 1e9
                )
                ui.number(min=0, step=0.0001, suffix="[nA]").bind_value(
                    auto_lower_limit, "value"
                ).bind_enabled_from(auto_current_range, "value").on(
                    "update:model-value",
                    lambda: self.settings_handler.change_setting(
                        "current_range_auto_lower_limit",
                        auto_lower_limit.get_value_in_Amp(),
                    ),
                    throttle=1.0,
                ).props(
                    props_input
                )

        with ui.card().classes("w-full mb-2"):
            ui.label("Integration settings")
            ui.separator()
            with ui.grid(columns=2).classes(
                "w-full gap-2 justify-items-left items-center p-1"
            ):
                ui.label("Aperture integration time: ")
                ui.number(min=0, step=0.0001, suffix="[s]").bind_value(
                    self.settings_handler.settings, "aperture_integration_time"
                ).on(
                    "update:model-value",
                    self.settings_handler.settings_changed,
                    throttle=1.0,
                ).props(
                    props_input
                )

                ui.label("Continuous Measurement Interval: ")
                ui.number(min=0.000001, step=10, suffix="[s]").bind_value(
                    self.settings_handler.settings, "continuous_measurement_interval"
                ).bind_enabled_from(app.storage.general, setting_continous_measurement).on(
                    "update:model-value",
                    self.settings_handler.settings_changed,
                    throttle=1.0,
                ).props(
                    props_input
                )

        with ui.card().classes("w-full my-2"):
            self.file_handler.alternative_filename_ui()
            with ui.grid(columns=4).classes("w-full justify-items-stretch p-4"):
                self.file_handler.download_file_button_ui()
                self.file_handler.save_download_clear_button_ui()
                ui.button(
                    "Show current data",
                    on_click=self.show_current_data_in_new_window,
                ).props(props_button)
                self.file_handler.delete_file_button_ui()

        with ui.card().classes("w-full mb-2"):
            self.file_handler.create_ui()

        with ui.expansion("Testing", icon="bug_report").classes(add="w-full"):
            ui.button(
                "Test Get Settings", on_click=lambda: self.pipe.send("get_settings")
            ).props(props_button)

    @ui.refreshable
    def main_page_ui(self):
        ui.label("Main Page Ion Chamber UI")


class ReactiveNumber:
    def __init__(self, value):
        self.value = value  # if current then value is in nanoAmpere

    def get_value_in_Amp(self):
        return self.value * 1e-9
