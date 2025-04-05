#!/usr/bin/env python3

import logging
from pathlib import Path
from nicegui import ui, app, run
from static.global_ui_props import *
from util.connection_manager_base import ConnectionManagerBase


logger = logging.getLogger()
work_dir = Path(__file__).parent


class FlashUI:
    def __init__(self, connection_managers: list[ConnectionManagerBase]) -> None:
        # remove the stages connection manager
        self.connection_managers = connection_managers
        self.connection_managers_dict = dict()
        for m in self.connection_managers:
            self.connection_managers_dict[m] = m.name

        self.selected_c_managers: list[ConnectionManagerBase] = []

    async def one_flash_please(self):
        if len(self.selected_c_managers) == 0:
            self.log_and_notify("Please select a components first!")
            return
        if not self.check_all_healthy():
            ui.notify("Please ensure that all component are connected!", type="warning", position="top", multi_line=True)
            return
        
        for m in self.selected_c_managers:
            ui.timer(0.0001, m.component.one_flash_please, once=True)

    
    def reset_components(self):
        self.selected_c_managers.clear()
        self.create_ui.refresh() # pylint: disable=no-member
        self.create_selected_ui.refresh() # pylint: disable=no-member

    @ui.refreshable
    def create_ui(self):
        with ui.card().classes("w-full mb-2"):
            with ui.row(wrap=False).classes("w-full items-center flex p-1"):

                with ui.row(wrap=False).classes("m-1 p-4 w-full items-center"):
                    ui.label("Flash UI - create FLASH -> ").style("font-size: 20px; font-weight: bold;")

                    ui.button("One Flash Please", on_click=self.one_flash_please, color="positive").classes("m-1").props(props_button)


                ui.space()


                def callback(e):
                    if e.value in self.selected_c_managers:
                        ui.notify(f"Component {e.value.name} already selected", type="warning", position="top", multi_line=True)
                    else:
                        self.selected_c_managers = e.value
                    self.create_selected_ui.refresh() # pylint: disable=no-member
                
                    
                with ui.row(wrap=False).classes("m-1 p-4 w-full items-center"):
                    ui.label("To add a component, select from the dropdown:").style("font-size: 14px; font-weight: bold;")
                    ui.select(self.connection_managers_dict, multiple=True, label='Component', value=self.selected_c_managers, on_change=callback).classes('w-64').props(props_select + ' use-chips').tooltip("Note that more than 2 components can lead to visual clutter and clipping in the ui ...")
                    
                ui.button("Reset Components", on_click=self.reset_components).classes("m-1").props(props_button)
            
        self.create_selected_ui()

    @ui.refreshable
    def create_selected_ui(self):
        # make it a splitter if there are exactly 2 components selected, else row them
        if len(self.selected_c_managers) == 2:
            self.two_devices_ui()
        else:
            with ui.row(wrap=False).classes("w-full justify-between p-1"):
                for m in self.selected_c_managers:
                    with ui.element().classes("m-1 p-4 w-full justify-center"):
                        m.create_ui()

       
    def two_devices_ui(self):
        with ui.splitter(value=50).classes("w-full justify-center") as splitter:
            with splitter.before:
                with ui.element().classes("m-1 p-4 w-full justify-center"):
                    self.selected_c_managers[0].create_ui()

            with splitter.after:
                with ui.element().classes("m-1 p-4 w-full justify-center"):
                    self.selected_c_managers[1].create_ui()


    def check_all_healthy(self):
        for m in self.selected_c_managers:
            if not m.healthy.value:
                return False
        return True

    
    def log_and_notify(self, message: str):
        logger.info(message)
        ui.notify(message)