#!/usr/bin/env python3

import logging
from pathlib import Path

import serial.tools.list_ports  # type: ignore
from components.chopperwheel.cw_component import CWComponent
from controllers import ChopperWheel
from nicegui import ui
from util.connection_manager_base import ConnectionManagerBase
from util.data_file_handler import DataFileHandler
from util.settings_handler import SettingsHandler
from static.global_ui_props import props_select

logger = logging.getLogger()
main_working_directory = Path(__file__).parent.parent


class CWConnectionManager(ConnectionManagerBase):
    def __init__(self):
        super().__init__()
        self.name = "Chopper Wheel"
        self.target = ChopperWheel
        self.settings_handler = SettingsHandler(
            "cw_settings.json", self.pipe, additional_path="cw"
        )
        self.data_file_handler = DataFileHandler(
            self.pipe,
            self.settings_handler,
            additional_path="cw",
            headers=["timestamp", "velocity", "angular_position"],
        )
        self.component: CWComponent = CWComponent(
            self.pipe, self.data_file_handler, self.settings_handler
        )
        self.ports = [port.device for port in serial.tools.list_ports.comports()]
        self.status_data = {"are_we_home_yet": "I don't know yet"}

    @ui.refreshable
    def connection_menu_ui(self):
        with ui.card().classes("w-full mb-2"):
            with ui.row().classes("w-full items-center no-wrap"):
                ui.label("CW: ")
                ui.select(
                    self.ports,
                    value=self.address,
                    label="Select port",
                    on_change=self.connect_to_address,
                    with_input=True,
                ).props(props_select)
                self.health_check_indicator()

    @ui.refreshable
    def main_page_ui(self):
        self.component.main_page_ui()

    @ui.refreshable
    def create_ui(self):
        ui.label("Chopper Wheel Control Panel").style(
            "font-size: 20px; font-weight: bold; margin-bottom: 20px;"
        )
        self.connection_menu_ui()

        with ui.grid(columns=2, rows=1).classes("gap-2"):
            ui.label("Motor is at Home position: ")
            self.home_position_label = ui.label("I don't know yet").bind_text_from(
                self, "status_data", backward=lambda x: str(x["are_we_home_yet"])
            )

        self.component.create_ui()
