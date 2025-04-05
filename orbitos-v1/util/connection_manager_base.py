#!/usr/bin/env python3
import logging.config
from multiprocessing import Pipe, Process
import asyncio

from nicegui import ui
from util.component_base import ComponentBase
from util.connection_status_chip import ConnectionStatusChip
from util.controller_base import ControllerBase
from util.data_file_handler import DataFileHandler
from util.settings_handler import SettingsHandler

logger = logging.getLogger()


class ConnectionManagerBase:
    def __init__(self):
        self.name: str = "Base Connection Manager"
        self.pipe, self.child_pipe = Pipe()
        self.process: Process = None  # type: ignore
        self.target: type[ControllerBase]
        self.component: ComponentBase
        self.settings_handler: SettingsHandler
        self.data_file_handler: DataFileHandler
        self.address: str = None  # type: ignore
        self.healthy: ReactiveHealthIndicator = ReactiveHealthIndicator(False)
        self.status_data = None
        self.status_data_timer = ui.timer(1.2, self.recv_status_data, active=False)

    def connection_menu_ui(self):
        raise NotImplementedError

    def create_ui(self):
        raise NotImplementedError

    def main_page_ui(self):
        raise NotImplementedError

    @ui.refreshable
    def health_check_indicator(self):
        self.chip = ConnectionStatusChip(self.healthy)

    async def recv_status_data(self):
        if self.pipe.poll(timeout=self.status_data_timer.interval - 0.2):
            while self.pipe.poll():
                answer = self.pipe.recv()
            self.healthy.value = bool(answer["healthy"])
            self.status_data = answer["status_data"]
        else:
            self.healthy.value = False

        self.chip.update()
        self.health_check_indicator.refresh()  # pylint: disable=no-member

    def set_dark_mode(self, value: bool):
        self.component.set_dark_mode(value)

    def connect_to_address(self, e):
        self.address = e.value
        self.start_process()
        self.connection_menu_ui.refresh()  # pylint: disable=no-member
        self.main_page_ui.refresh()  # pylint: disable=no-member
        self.create_ui.refresh()  # pylint: disable=no-member
        logger.info("Selected port: %s", self.address)
        ui.timer(0.01, self.wait_for_connection, once=True)

    def start_process(self):
        self.kill_process()
        if self.address and self.child_pipe and self.settings_handler:
            self.process = Process(
                target=self.target,
                args=(self.address, self.child_pipe, self.settings_handler),
            )
            self.process.start()
            self.status_data_timer.active = True
        else:
            logger.error(
                "Cannot start process. Missing address, child_pipe or file_handler"
            )

    def refresh_stuff(self):
        self.connection_menu_ui.refresh()  # pylint: disable=no-member
        self.main_page_ui.refresh()  # pylint: disable=no-member
        self.create_ui.refresh()  # pylint: disable=no-member

    def kill_process(self):
        if self.process:
            self.healthy.value = False
            self.process.kill()
            self.process.join()
            self.process = None  # type: ignore
            self.address = None  # type: ignore
            self.status_data_timer.active = False
            self.refresh_stuff()

    async def wait_for_connection(self, name="device", condition_func=lambda: False):
        n = ui.notification(timeout=None, message=f"Connecting to {name} ...", close_button=True, position="top")

        while not (self.healthy.value or condition_func()):
            n.spinner = True
            await asyncio.sleep(0.3)
        
        n.message = "Connected!"
        n.type = "positive"
        n.spinner = False
        await asyncio.sleep(1)
        n.dismiss()

class ReactiveHealthIndicator:
    def __init__(self, value: bool):
        self.value: bool = value
