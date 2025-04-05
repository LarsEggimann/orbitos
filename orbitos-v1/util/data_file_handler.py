#!/usr/bin/env python3
"""
This module represents a chopper wheel device.
"""
import csv
import logging
import os
import shutil
import time
from multiprocessing.connection import Connection
from pathlib import Path
import tempfile
from static.global_ui_props import *

from nicegui import ui

from util.settings_handler import SettingsHandler

logger = logging.getLogger()


class DataFileHandler:
    def __init__(
        self,
        pipe_connection: Connection,
        settings_handler: SettingsHandler,
        additional_path: str = "",
        prefix: str = "",
        postfix: str = "",
        headers: list[str] = [],
    ) -> None:
        self.last_mod_time = 0.0
        self.last_position_read = 0
        self.settings_handler = settings_handler
        self.working_directory = Path(__file__).parent.parent
        self.base_path = Path(str(self.working_directory / "data" / additional_path))
        self.prefix = prefix
        self.postfix = postfix
        self.timestamp = ""
        self.pipe = pipe_connection
        self.additional_path = additional_path
        self.headers = headers
        self.full_filename = ""
        self.read_filename_if_file_exists()
        self.full_filename_old = self.full_filename
        self.filename = Path(self.full_filename).name
        self.set_been_pressed = False

        self.filename_of_download_inputfield = ""

    def change_full_filename(self, new_filename):
        self.full_filename = str(new_filename)
        self.filename = str(Path(self.full_filename).name)

    def read_filename_if_file_exists(self):
        prov_filename = self.settings_handler.settings["filename"]
        if os.path.exists(prov_filename):
            self.change_full_filename(prov_filename)
            self.log_and_notify(
                f"{self.additional_path} datasource set to {self.full_filename}"
            )
        else:
            self.generate_filename()
            self.create_file()

    def generate_filename(self):
        timestamp = time.strftime("%Y-%m-%d")
        filename = os.path.join(
            self.base_path, f"{self.prefix}{timestamp}{self.postfix}.csv"
        )
        self.change_full_filename(filename)
        self._ensure_directory_exists()
        self.write_new_filename_to_settings()
        return self.full_filename

    def create_file(self):
        # if the file already exists, log and do nothing
        if os.path.exists(self.full_filename):
            self.log_and_notify(
                f"File {self.full_filename} already exists, appending data."
            )
            return
        with open(self.full_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)

    def _delete_file(self):
        self.last_position_read = 0
        os.remove(self.full_filename)
        self.create_file()
        self.log_and_notify(f"File {self.full_filename} has been emptied.")

    def _ensure_directory_exists(self):
        os.makedirs(os.path.dirname(self.full_filename), exist_ok=True)

    def _is_it_a_new_filename(self):
        if self.full_filename != self.full_filename_old:
            self.last_position_read = 0
            self.full_filename_old = self.full_filename
            return True
        return False

    def new_data_or_new_file(self):
        if not os.path.exists(self.full_filename):
            self._ensure_directory_exists()
        if self._is_it_a_new_filename():
            return True
        mod_time = os.path.getmtime(self.full_filename)
        if mod_time > self.last_mod_time:
            self.last_mod_time = mod_time
            return True
        return False

    def delete_file_button_ui(self):
        with ui.dialog() as dialog, ui.card():
            ui.label(f'Are you sure you want to delete "{self.full_filename}"?')
            with ui.row().classes("w-full justify-center items-center"):

                def confirm_action():
                    dialog.close()
                    self._delete_file()

                ui.button("Yes!", on_click=confirm_action).props(props_button)
                ui.button("No!", on_click=dialog.close).props(props_button)

        ui.button("Delete data", on_click=dialog.open, color="warning").props(
            props_button
        ).tooltip("Delete the current content of data file.")

    def copy_current_data_to_new_temp_file(self):
        ending = time.strftime("%H-%M-%S")
        copy_filename = self.full_filename.replace(".csv", f"_{ending}.csv")
        copy_filename = os.path.join(
            tempfile.gettempdir(), os.path.basename(copy_filename)
        )
        shutil.copyfile(self.full_filename, copy_filename)
        self.log_and_notify(f"File {self.full_filename} has been copied to a new file.")
        return copy_filename

    def copy_current_data_to_new_file(self):
        copy_filename = self.get_current_full_filename()
        try:
            shutil.copyfile(self.full_filename, copy_filename)
            self.set_filename(copy_filename)
        except Exception as e:
            self.log_and_notify(f"Could not copy file to {copy_filename}. Error: {e}")

    def alternative_filename_ui(self):
        size_limit = 20
        leave_me_be = False
        with ui.dialog() as dialog, ui.card():
            ui.restructured_text(
                f"Your filename is a bit long, **Alex**. You may want to make a note instead. Are you sure you want such a long filename?"
            )
            with ui.row().classes("w-full justify-center items-center"):

                def confirm():
                    nonlocal leave_me_be
                    dialog.close()
                    leave_me_be = True

                ui.button("Yes, leave me be!", on_click=confirm).props(props_button)
                ui.button(
                    "No, you're right and I'm sorry.", on_click=dialog.close
                ).props(props_button)

        def on_change():
            if len(input.value) > size_limit and not leave_me_be:
                dialog.open()
            self.filename_of_download_inputfield = input.value

        input = (
            ui.input(
                label="Filename of the downloaded file",
                value=self.filename_of_download_inputfield,
                on_change=on_change,
            )
            .props(props_input)
            .classes("w-full")
        )

    def download_file(self, filename=None):
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")

        if self.filename_of_download_inputfield != "":
            download_filename = (
                str(timestamp) + "_" + self.filename_of_download_inputfield + ".csv"
            )
        else:
            download_filename = str(timestamp) + "_" + self.filename

        if filename is None:
            filename = self.full_filename

        ui.download(src=filename, filename=download_filename)

    def download_file_button_ui(self):
        ui.button("Download data", on_click=self.download_file, color="positive").props(
            props_button
        ).tooltip("Download the current data file.")

    def save_download_clear_button_ui(self):
        ui.button("Save, Download and Clear", on_click=self.save_download_clear).props(
            props_button
        ).tooltip(
            f"Save current data to a new file with timestamp under {self.base_path}, download it and clear the current file."
        )

    def save_download_clear(self):
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")

        copy_filename = Path(self.full_filename).with_name(
            f"{timestamp}__{self.filename}"
        )
        try:
            shutil.copyfile(self.full_filename, copy_filename)
            self.download_file(filename=copy_filename)
            self._delete_file()
        except Exception as e:
            self.log_and_notify(f"Could not copy file to {copy_filename}. Error: {e}")

    def log_and_notify(self, message):
        """
        Log and notify the user about a message.
        """
        logger.info(message)
        ui.notify(message)

    def set_filename(self, new_full_filename=None):
        if new_full_filename is None:
            new_full_filename = self.get_current_full_filename()
        self.change_full_filename(new_full_filename)
        self.set_been_pressed = True
        self.create_ui.refresh()  # pylint: disable=no-member
        self.create_file()
        self.pipe.send(f"setting filename {self.full_filename}")
        self.write_new_filename_to_settings()
        self.log_and_notify(
            f"{self.additional_path} datasource set to {self.full_filename}"
        )

    def write_new_filename_to_settings(self):
        self.settings_handler.change_setting("filename", self.full_filename)

    def get_current_full_filename(self):
        new = str(
            Path(Path(self.full_filename).parent / self.input_field.value).with_suffix(
                ".csv"
            )
        )
        return new

    def reset_set_been_pressed(self):
        self.set_been_pressed = False

    @ui.refreshable
    def create_ui(self):
        ui.label("File Settings:")
        ui.separator()
        with ui.row().classes("w-full items-center no-wrap p-1"):
            ui.label("Filename: ")
            self.input_field = (
                ui.input(
                    value=self.filename,
                    on_change=self.reset_set_been_pressed,
                    validation={
                        "Confirm new Path with Set or Copy": lambda x: self.set_been_pressed
                    },
                )
                .classes("w-full")
                .props(props_input)
            )
            ui.button("Set data source", on_click=self.set_filename).props(
                props_button
            ).tooltip(
                "Set the filename as data source. The plot shows the new file and new data will be added to the new file. The old file will be kept."
            )
            ui.button(
                "Copy data to file", on_click=self.copy_current_data_to_new_file
            ).props(props_button).tooltip(
                "Copy current data to new file and set new file as data source. The plot shows the new file and new data will be added to the new file. The old file will be kept."
            )
