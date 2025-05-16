#!/usr/bin/env python3

import logging.config
from util.settings_handler import SettingsHandler
from multiprocessing.connection import Connection

logger = logging.getLogger()


class ControllerBase:
    def __init__(
        self, address: str, pipe: Connection, settings_handler: SettingsHandler
    ):
        self.pipe = pipe
        self.settings_handler = settings_handler
        self.filename = settings_handler.settings["filename"]
        self.address = address
        self.send_status_data_timeout = 5  # seconds
        self.send_settings_within_next_update = False

        # self.clear_pipe()

    def clear_pipe(self):
        while self.pipe.poll():
            self.pipe.recv()
