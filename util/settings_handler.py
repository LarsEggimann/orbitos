#!/usr/bin/env python3
"""
This module represents a chopper wheel device.
"""
import logging
from multiprocessing.connection import Connection
import os
import shutil
from pathlib import Path
import orjson

logger = logging.getLogger()


class SettingsHandler:
    def __init__(
        self,
        filename: str,
        pipe: Connection,
        additional_path: str = "",
    ) -> None:
        self.last_mod_time = 0.0
        self.working_directory = Path(__file__).parent.parent
        self.filename = Path(
            str(self.working_directory / "settings" / additional_path / filename)
        )
        self.settings: dict = self.read_settings()
        self.previous_settings = self.settings.copy()
        self.filename_old = self.filename
        self.pipe = pipe

    def read_settings(self):
        # check if the file exists
        if not os.path.isfile(self.filename):
            self._ensure_directory_exists()
            self.reset_to_default_settings()
        with open(self.filename, "r", encoding="utf-8") as f:
            self.settings = orjson.loads(f.read())
        return self.settings

    def change_setting(self, key: str, value):
        self.settings[key] = value
        self.settings_changed()

    def settings_changed(self):
        self._write_settings()
        if self.pipe:
            self.pipe.send("settings_changed")

    def _write_settings(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(orjson.dumps(self.settings, option=orjson.OPT_INDENT_2).decode())
        self.log(f"Settings have been updated in {self.filename}.")

    def reset_to_default_settings(self):
        if os.path.isfile(self.filename):
            os.remove(self.filename)
        default_name = str(self.filename).replace(".json", "_default.json")
        shutil.copy(default_name, self.filename)
        self.log(f"Settings have been reset to default in {self.filename}.")

    def _ensure_directory_exists(self):
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)

    def _is_it_a_new_filename(self):
        """
        Check if the filename has changed.
        """
        if self.filename != self.filename_old:
            self.filename_old = self.filename
            return True
        return False

    def new_data_or_new_file(self):
        """
        Check if the file has been modified.
        """
        if not os.path.exists(self.filename):
            self._ensure_directory_exists()
        if self._is_it_a_new_filename():
            return True
        mod_time = os.path.getmtime(self.filename)
        if mod_time > self.last_mod_time:
            self.last_mod_time = mod_time
            return True
        return False

    def get_changed_settings(self):
        changed_settings = {}
        for key, value in self.settings.items():
            if self.previous_settings[key] != value:
                changed_settings[key] = value
        self.previous_settings = self.settings.copy()
        return changed_settings

    def log(self, message):
        """
        Log and notify the user about a message.
        """
        logger.debug(message)
        # ui.notify(message)
