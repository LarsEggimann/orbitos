#!/usr/bin/env python3

import logging
from pathlib import Path

from components.stages.stages_component import StagesComponent
from nicegui import ui
from controllers.stage.arcus_performax_DMX_J_SA_stage import ArcusPerformaxDMXJSAStage
from util.connection_manager_base import ConnectionManagerBase
from util.connection_status_chip import ConnectionStatusChip
from util.data_file_handler import DataFileHandler
from util.settings_handler import SettingsHandler

from static.global_ui_props import props_select

logger = logging.getLogger()
main_working_directory = Path(__file__).parent.parent


class StagesConnectionManager(ConnectionManagerBase):
    def __init__(self, additional_path="stages", name="Stages"):
        super().__init__()
        self.name = name
        self.settings_handler = SettingsHandler(
            "stages_settings.json", None, additional_path=additional_path
        )
        self.data_file_handler = DataFileHandler(
            None,
            self.settings_handler,
            additional_path=additional_path,
            headers=["time", "x", "y"],
        )

        self.stage_x = ArcusPerformaxDMXJSAStage("Stage X")
        self.stage_y = ArcusPerformaxDMXJSAStage("Stage Y")

        self.healthy_x: ReactiveHealthIndicator = ReactiveHealthIndicator(False)
        self.healthy_y: ReactiveHealthIndicator = ReactiveHealthIndicator(False)

        self.component: StagesComponent = StagesComponent(
            self.data_file_handler, self.settings_handler, self.stage_x, self.stage_y
        )

        self.check_health_x_timer = ui.timer(1, self.check_health_x, active=False)
        self.check_health_y_timer = ui.timer(1, self.check_health_y, active=False)

        self.port_x = None
        self.port_y = None

        self.select_x = None
        self.select_y = None

    @ui.refreshable
    def connection_menu_ui(self):
        ui.label("Stages Connections")
        with ui.row().classes("w-full items-center no-wrap"):
            ui.label("X: ")
            self.select_x = ui.select(
                options=self.stage_x.list_usb_performax_devices(),
                label="Select device",
                value=self.port_x,
                on_change=self.connect_x,
                with_input=True,
            ).props(props_select)
            self.health_check_indicator_x()

        with ui.row().classes("w-full items-center no-wrap"):
            ui.label("Y: ")
            self.select_y = ui.select(
                options=self.stage_x.list_usb_performax_devices(),
                label="Select device",
                value=self.port_y,
                on_change=self.connect_y,
                with_input=True,
            ).props(props_select)
            self.health_check_indicator_y()

    @ui.refreshable
    def health_check_indicator_x(self):
        self.chip_x = ConnectionStatusChip(self.healthy_x)

    @ui.refreshable
    def health_check_indicator_y(self):
        self.chip_y = ConnectionStatusChip(self.healthy_y)

    @ui.refreshable
    def main_page_ui(self):
        self.component.main_page_ui()

    @ui.refreshable
    def create_ui(self):
        self.connection_menu_ui()
        self.component.create_ui()

    async def check_health_x(self):
        self.healthy_x.value = self.stage_x.is_healthy()
        self.chip_x.update()
        self.health_check_indicator_x.refresh()  # pylint: disable=no-member

    async def check_health_y(self):
        self.healthy_y.value = self.stage_y.is_healthy()
        self.chip_y.update()
        self.health_check_indicator_y.refresh()  # pylint: disable=no-member

    def connect_x(self, e):
        idx = e.value
        self.stage_x.connect(idx)
        self.port_x = e.value
        logger.info("Selected port: %s", e.value)
        self.refresh_stuff()
        self.check_health_x_timer.active = True
        ui.timer(0.01, lambda: self.wait_for_connection("x_stage", condition_func=lambda: self.healthy_x.value), once=True)

    def connect_y(self, e):
        idx = e.value
        self.stage_y.connect(idx)
        self.check_health_y_timer.active = True
        self.port_y = e.value
        logger.info("Selected port: %s", e.value)
        self.refresh_stuff()
        ui.timer(0.01, lambda: self.wait_for_connection("y_stage", condition_func=lambda: self.healthy_y.value), once=True)

    def refresh_stuff(self):
        self.connection_menu_ui.refresh()  # pylint: disable=no-member
        self.main_page_ui.refresh()  # pylint: disable=no-member
        self.create_ui.refresh()  # pylint: disable=no-member

    def start_process(self):
        raise NotImplementedError

    def kill_process(self):
        self.stage_x.close()
        self.stage_y.close()
        self.check_health_x_timer.active = False
        self.check_health_y_timer.active = False
        self.healthy_x.value = False
        self.healthy_y.value = False
        self.port_x = None
        self.port_y = None



    def set_dark_mode(self, value: bool):
        self.component.set_dark_mode(value)


class ReactiveHealthIndicator:
    def __init__(self, value: bool):
        self.value: bool = value
