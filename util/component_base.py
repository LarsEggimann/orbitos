#!/usr/bin/env python3

from multiprocessing.connection import Connection
import logging

import plotly.graph_objects as go  # type: ignore
from nicegui import ui
from util.data_file_handler import DataFileHandler
from util.settings_handler import SettingsHandler

logger = logging.getLogger()

class ComponentBase:
    def __init__(
        self,
        pipe: Connection,
        file_handler: DataFileHandler,
        settings_handler: SettingsHandler,
    ):
        self.pipe = pipe
        self.file_handler = file_handler
        self.settings_handler = settings_handler
        self.plot_plotly: go.Figure
        self.plot_nicegui: ui.plotly
        self.dark_mode: bool

        self.initial_settings: dict = {}
        
    def create_ui(self):
        raise NotImplementedError

    def main_page_ui(self):
        raise NotImplementedError

    def plot(self):
        raise NotImplementedError
    
    async def one_flash_please(self):
        logger.info("oops, this is not implemented in this component")

    def set_dark_mode(self, value: bool):
        self.dark_mode = value
        try:
            self.plot_plotly.update_layout(
                go.Layout(template="plotly_dark" if value else "seaborn")
            )
            self.plot_nicegui.update()
        except AttributeError:
            pass
