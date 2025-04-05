#!/usr/bin/env python3

import logging.config

from components.chopperwheel import CWConnectionManager
from components.electrometer import EMConnectionManager
from components.flash_ui import FlashUI
from components.combined_data_view import CombinedDataView
from static.global_ui_props import *
from nicegui import ui
from components.stages.stages_connection_manager import StagesConnectionManager
from components.lab_notes import LabNotes

from util.connection_manager_base import ConnectionManagerBase

logger = logging.getLogger()


class DeviceManager:
    def __init__(self) -> None:
        self.cw_connection_manager: CWConnectionManager = CWConnectionManager()
        self.em_connection_manager: EMConnectionManager = EMConnectionManager(
            default_address="192.168.113.72",
            additional_path="em1",
            name="Electrometer 1",
        )
        self.em_connection_manager_2: EMConnectionManager = EMConnectionManager(
            default_address="192.168.113.73",
            additional_path="em2",
            name="Electrometer 2",
        )

        self.stages_connection_manager = StagesConnectionManager()

        self.connection_managers: list[ConnectionManagerBase] = [
            self.cw_connection_manager,
            self.em_connection_manager,
            self.em_connection_manager_2,
            self.stages_connection_manager,
        ]

        self.lab_notes_component = LabNotes(self.connection_managers)

        self.connection_managers_reduced = [self.cw_connection_manager,
            self.em_connection_manager,
            self.em_connection_manager_2
            ]

        self.flash_ui_component = FlashUI(self.connection_managers_reduced)

        self.combined_data_view = CombinedDataView(self.connection_managers_reduced)

    def reset_connections(self):
        for m in self.connection_managers:
            m.kill_process()
            m.connection_menu_ui.refresh()  # pylint: disable=no-member
        logger.info("Connections reset")

    @ui.refreshable
    def chopper_wheel_ui(self):
        self.cw_connection_manager.create_ui()

    @ui.refreshable
    def ion_chamber_ui(self):
        ui.label("Electrometer 1 Control Panel").style(
            "font-size: 20px; font-weight: bold; margin-bottom: 20px;"
        )
        self.em_connection_manager.create_ui()

    @ui.refreshable
    def electrometer_ui(self):
        ui.label("Electrometer 2 Control Panel").style(
            "font-size: 20px; font-weight: bold; margin-bottom: 20px;"
        )
        self.em_connection_manager_2.create_ui()

    @ui.refreshable
    def electrometers_ui(self):
        def on_change():
            self.em_connection_manager.component.plot.refresh()
            self.em_connection_manager_2.component.plot.refresh()

        with ui.splitter(on_change=on_change).classes("w-full") as splitter:
            with splitter.before:
                with ui.element().classes("w-full p-4"):
                    self.ion_chamber_ui()
            with splitter.after:
                with ui.element().classes("w-full p-4"):
                    self.electrometer_ui()

    @ui.refreshable
    def combo_view(self):
        ui.label("Combo View is still under construction")

    @ui.refreshable
    def create_device_manager_ui(self):
        for m in self.connection_managers:
            m.connection_menu_ui()
        ui.button("Reset Connections", on_click=self.reset_connections).props(
            props_button
        )
        
    @ui.refreshable
    def main_page_connection_menu(self):
        for m in self.connection_managers:
            m.connection_menu_ui()

    @ui.refreshable
    def main_page_devices_ui(self):
        for m in self.connection_managers:
            m.main_page_ui()

    @ui.refreshable
    def stages_ui(self):
        self.stages_connection_manager.create_ui()

    @ui.refreshable
    def lab_notes_ui(self):
        self.lab_notes_component.create_ui()

    @ui.refreshable
    def flash_ui(self):
        self.flash_ui_component.create_ui()

    @ui.refreshable
    def combined_data_view_ui(self):
        self.combined_data_view.create_ui()

    def set_dark_mode(self, value: bool):
        for m in self.connection_managers:
            m.set_dark_mode(value)
        
        self.combined_data_view.set_dark_mode(value)


device_manager = DeviceManager()
