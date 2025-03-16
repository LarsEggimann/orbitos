#!/usr/bin/env python3

import logging
from pathlib import Path

from components.electrometer.ic_component import ICComponent
from controllers import KeysightEM
from nicegui import ui
from util.connection_manager_base import ConnectionManagerBase
from util.data_file_handler import DataFileHandler
from util.settings_handler import SettingsHandler
from static.global_ui_props import *

logger = logging.getLogger()
main_working_directory = Path(__file__).parent.parent


class EMConnectionManager(ConnectionManagerBase):
    def __init__(self, default_address="", additional_path="em", name="Electrometer"):
        super().__init__()
        self.name = name
        self.target = KeysightEM
        self.settings_handler = SettingsHandler(
            "em_settings.json", self.pipe, additional_path=additional_path
        )
        self.data_file_handler = DataFileHandler(
            self.pipe,
            self.settings_handler,
            additional_path=additional_path,
            headers=["time", "current"],
        )
        self.component: ICComponent = ICComponent(
            self.pipe, self.data_file_handler, self.settings_handler, name
        )
        self.address = default_address

    @ui.refreshable
    def connection_menu_ui(self):
        with ui.card().classes("w-full mb-2"):
            with ui.row().classes("w-full items-center no-wrap"):
                ui.label("IC: ")
                label = ui.select(
                    options=["192.168.113.72", "192.168.113.73"],
                    label="ip address",
                    value=self.address,
                ).props(props_select)
                ui.button(
                    "Connect", on_click=lambda: self.connect_to_address(label)
                ).classes("p-1").props(props_button)
                self.health_check_indicator()

    @ui.refreshable
    def main_page_ui(self):
        self.component.main_page_ui()

    @ui.refreshable
    def create_ui(self):
        self.connection_menu_ui()
        self.component.create_ui()
