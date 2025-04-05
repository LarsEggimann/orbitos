#!/usr/bin/env python3

import logging
from pathlib import Path
import time
from nicegui import ui, app
import orjson
from static.global_ui_props import *
from util.connection_manager_base import ConnectionManagerBase

import os

logger = logging.getLogger()
work_dir = Path(__file__).parent


class LabNotes:
    def __init__(self, connection_managers: list[ConnectionManagerBase]) -> None:
        self.path = Path(work_dir / "lab_notes.json")

        self.note_types = ["Simple Note", "Incident", "Other"]

        self.notes: list = self.load_notes()

        self.connection_managers = connection_managers
        self.connection_managers_dict = dict()
        for m in self.connection_managers:
            self.connection_managers_dict[m] = m.name

    @ui.refreshable
    def create_ui(self):
        self.load_notes()

        with ui.splitter(value=50).classes("w-full") as splitter:
            with splitter.before:
                with ui.element().classes("m-1 p-4 w-full justify-center"):
                    self.create_note_ui()

            with splitter.after:
                with ui.element().classes("m-1 p-4 w-full"):
                    self.show_notes()

    def delete_note(self, index):
        def delete():
            def confirm_delete():
                self.notes.pop(index)
                with open(self.path, "w", encoding="utf-8") as f:
                    f.write(
                        orjson.dumps(self.notes, option=orjson.OPT_INDENT_2).decode()
                    )
                ui.notify("note deleted")
                self.create_ui.refresh()  # pylint: disable=no-member
            with ui.dialog() as dialog, ui.card():
                ui.label(f"Are you sure you want to delete the note number {index}?")
                with ui.row().classes("w-full justify-center items-center"):
                    ui.button("Yes, delete it!", on_click=confirm_delete).props(
                        props_button
                    )
                    ui.button("No, I was too fast!", on_click=dialog.close).props(
                        props_button
                    )
            dialog.open()
        return delete

    def load_note(self, index):
        def load():
            note = self.notes[index]
            self.note_type.value = note["type"]
            self.timestamp.value = time.strftime("%Y-%m-%d %H:%M:%S")
            self.description.value = note["description"]
        return load
    
    def edit_note(self, index):            
        def edit():
            note_to_edit = self.notes[index]
            with ui.dialog() as dialog, ui.card().classes("m-1 p-4 w-full justify-center"):
                ui.label("Edit note number " + str(index))
                note_type = (
                    ui.select(
                            label="Note Type",
                            value=note_to_edit["type"],
                            options=self.note_types,
                            with_input=True,
                        )
                        .props(props_select)
                        .classes("mb-4 w-full")
                    )
                timestamp = (
                        ui.input(label="Timestamp", value=note_to_edit["timestamp"])
                        .props(props_input)
                        .classes("mb-4 w-full")
                    )
                description = (
                        ui.textarea("Description, markdown formatting", value=note_to_edit["description"])
                        .props("input-style=height:350px").classes("w-full")
                    )
                
                def save():
                    note = self.build_note(
                        note_type.value,
                        timestamp.value,
                        description.value,
                    )
                    self.notes[index] = note
                    self.save_note_to_file(note, edit=True)
                    ui.notify("note edited", type="positive")
                    dialog.close()
                    self.create_ui.refresh() # pylint: disable=no-member

                with ui.row(wrap=False).classes("w-full items-center justify-between"):
                    ui.button("Close", on_click=dialog.close).props(
                        props_button + "  outline"
                    )
                    ui.button("Save note", on_click=save, icon="save").props(props_button)

            dialog.open()
        return edit

    def preview_note(self):
        note = self.build_note(
            self.note_type.value,
            self.timestamp.value,
            self.description.value,
        )
        with ui.dialog() as dialog, ui.card():
            self.render_note(note)
            ui.button("Close", on_click=dialog.close).props(
                props_button + "  outline"
            ).classes("center")
        dialog.open()

    def render_note(self, note, i=None):
        with ui.card().classes("mb-4"):
            with ui.row(wrap=False).classes("w-full flex"):
                with ui.element().classes("grow"):
                    type = ui.label(f"Type: {note['type']}").style("font-weight: bold;")
                    if str(note["type"]).find("Incident") != -1:
                        type.style("color: red;")
                    timestamp = ui.label(f"Timestamp: {note['timestamp']}")
                    if note["timestamp_numb"] == 0:
                        timestamp.style("color: red;").set_text(
                            timestamp.text
                            + " (invalid timestamp, load and fromat the note to fix)"
                        )
                    ui.markdown(content=f"""{note['description']}""")
                if i is not None:
                    with ui.button(icon='more_vert').props(props_button + "outline").classes("mt-4"):
                        with ui.menu():
                            ui.menu_item('Load Note', self.load_note(i), auto_close=False).tooltip("Load note to edit fields")
                            ui.menu_item('Edit', self.edit_note(i), auto_close=False).tooltip("Edit note")
                            ui.separator()
                            o2 = ui.menu_item('Delete', self.delete_note(i), auto_close=False).tooltip("Delete note")
                            if str(note["type"]).find("Example") != -1:
                                o2.disable()

    def show_notes(self):
        ui.label("All notes").style(
            "font-size: 20px; font-weight: bold; margin-bottom: 20px;"
        )
        ui.separator().classes("mb-4")
        for i, note in enumerate(self.notes):
            self.render_note(note, i)

    async def submit(self):
        note = self.build_note(
            self.note_type.value,
            self.timestamp.value,
            self.description.value,
        )
        self.save_note_to_file(note)
        ui.notify("note submitted", type="positive")
        self.create_ui.refresh()  # pylint: disable=no-member        

    def create_note_ui(self):

        ui.label("Save a note").style(
            "font-size: 20px; font-weight: bold; margin-bottom: 20px;"
        )
        ui.separator().classes("mb-4")

        self.note_type = (
            ui.select(
                label="Note Type",
                value="Simple Note",
                options=self.note_types,
                with_input=True,
            )
            .props(props_select)
            .classes("mb-4")
        )
        self.timestamp = (
            ui.input(label="Timestamp", value=f"{time.strftime('%Y-%m-%d %H:%M:%S')}")
            .props(props_input)
            .classes("mb-4")
        )
        app.storage.general.get("lab_notes", "")
        self.description = (
            ui.textarea("Description, markdown formatting")
            .bind_value(app.storage.general, "labe_notes")
            .props("input-style=height:350px")
        )

        def load_settings_into_description():
            connection_manager: ConnectionManagerBase = selector.value
            settings = connection_manager.settings_handler.settings
            if "filename" in settings:
                settings.pop("filename")
            settings = orjson.dumps(settings, option=orjson.OPT_INDENT_2).decode()
            string_to_insert = f"###### {connection_manager.name} settings:\n"
            string_to_insert += f"```json\n{settings}\n```\n"
            self.description.value += string_to_insert

        with ui.element().classes("w-full  flex mt-2"):

            selector = ui.select(options=self.connection_managers_dict, label="Component", on_change=load_settings_into_description).props(props_select).classes("grow")
            ui.button("Load settings", on_click=load_settings_into_description).props(props_button).classes("mt-4 ml-4")

            ui.button("Preview note", on_click=self.preview_note).props(
                props_button
            ).classes("mt-4 ml-4").tooltip(
                "Preview the note before saving it, due to markdown formatting it might look different than expected"
            )
            ui.button("Save note", on_click=self.submit, icon="save").props(props_button).classes("mt-4 ml-4")

    def load_notes(self):

        if not os.path.isfile(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            self.notes = orjson.loads(f.read())

        self.notes = sorted(self.notes, key=lambda x: x["timestamp_numb"], reverse=True)
        return self.notes

    def save_note_to_file(self, note: list, edit=False):
        # self.load_notes()
        if not edit:
            self.notes.append(note)

        with open(self.path, "w", encoding="utf-8") as f:
            f.write(orjson.dumps(self.notes, option=orjson.OPT_INDENT_2).decode())

    def build_note(self, note_type, timestamp, description):
        note = {
            "type": note_type,
            "timestamp": timestamp,
            "description": description,
        }
        try:
            note["timestamp_numb"] = time.mktime(
                time.strptime(note["timestamp"], "%Y-%m-%d %H:%M:%S")
            )
        except:
            note["timestamp_numb"] = 0

        return note
