#!/usr/bin/env python3

import logging
from pathlib import Path
import asyncio
import numpy as np  # type: ignore
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
from skimage import io
from nicegui import events, ui, app
import orjson
from static.global_ui_props import *

import os

logger = logging.getLogger()
work_dir = Path(__file__).parent


class BugReporter:
    def __init__(self):
        self.path = Path(work_dir / "reports.json")

        self.report_types = ["Bug", "Feature Request", "Other"]

        self.status = ["Done", "In Progress", "To Do"]

        self.reports: list = self.load_reports()

    @ui.refreshable
    def create_ui(self):
        self.load_reports()

        with ui.splitter(value=50).classes("w-full") as splitter:
            with splitter.before:
                with ui.element().classes("m-1 p-4 w-full justify-center"):
                    self.create_report_ui()

            with splitter.after:
                with ui.element().classes("m-1 p-4 w-full"):
                    self.show_reports()

    def delete_report(self, index):
        def delete():
            def confirm_delete():
                self.reports.pop(index)
                with open(self.path, "w", encoding="utf-8") as f:
                    f.write(
                        orjson.dumps(self.reports, option=orjson.OPT_INDENT_2).decode()
                    )
                ui.notify("Report deleted")
                self.create_ui.refresh()  # pylint: disable=no-member

            with ui.dialog() as dialog, ui.card():
                ui.label(f"Are you sure you want to delete the report number {index}?")
                with ui.row().classes("w-full justify-center items-center"):
                    ui.button("Yes, delete it!", on_click=confirm_delete).props(
                        props_button
                    )
                    ui.button("No, I was too fast!", on_click=dialog.close).props(
                        props_button
                    )
            dialog.open()

        return delete
    
    def mark_as_done(self, index):
        def mark():
            def confirm_mark():
                self.reports[index]["status"] = "Done"
                with open(self.path, "w", encoding="utf-8") as f:
                    f.write(
                        orjson.dumps(self.reports, option=orjson.OPT_INDENT_2).decode()
                    )
                ui.notify("Report marked as Done")
                self.create_ui.refresh()  # pylint: disable=no-member
            
            with ui.dialog() as dialog, ui.card():
                ui.label(f"Are you sure you want to mark the report number {index} as Done?")
                with ui.row().classes("w-full justify-center items-center"):
                    ui.button("Yes, mark it as Done!", on_click=confirm_mark).props(
                        props_button
                    )
                    ui.button("No, I was too fast!", on_click=dialog.close).props(
                        props_button
                    )
            dialog.open()

        return mark

    def show_reports(self):
        ui.label("All Reports").style(
            "font-size: 20px; font-weight: bold; margin-bottom: 20px;"
        )
        ui.separator().classes("mb-4")
        done_reports = []
        for i, report in enumerate(self.reports):
            if report["status"] == "To Do":
                with ui.card().classes("mb-4"):
                    with ui.row(wrap=False).classes("w-full justify-between"):
                        with ui.element():
                            ui.label(f"Type: {report['type']}").style("font-weight: bold;")
                            ui.label(f"Description: {report['description']}")
                            ui.label(f"Steps to reproduce: {report['steps_to_reproduce']}")
                            ui.label(f"Expected behavior: {report['expected_behavior']}")

                        with ui.button(icon='more_vert').props(props_button + "outline").classes("mt-4"):
                            with ui.menu():
                                delete_item1 = ui.menu_item('Mark as Done', self.mark_as_done(i), auto_close=False)
                                delete_item2 = ui.menu_item('Delete', self.delete_report(i), auto_close=False)
                                if str(report["type"]).find("Example") != -1:
                                    delete_item1.disable()
                                    delete_item2.disable()

            else:
                done_reports.append(report)
        
        with ui.expansion("Done Reports", icon="bug_report").classes(add="w-full"):
            for i, report in enumerate(done_reports):
                with ui.card().classes("mb-4"):
                    with ui.element():
                        ui.label(f"Type: {report['type']}").style("font-weight: bold;")
                        ui.label(f"Description: {report['description']}")
                        ui.label(f"Steps to reproduce: {report['steps_to_reproduce']}")
                        ui.label(f"Expected behavior: {report['expected_behavior']}")

    async def submit(self):
        report = self.build_report(
            self.report_type.value,
            self.description.value,
            self.steps_to_reproduce.value,
            self.expected_behavior.value,
        )
        self.save_report_to_file(report)
        ui.notify("Report submitted", type="positive")
        self.create_ui.refresh()  # pylint: disable=no-member

    def create_report_ui(self):

        ui.label("Submit a report").style(
            "font-size: 20px; font-weight: bold; margin-bottom: 20px;"
        )
        ui.separator().classes("mb-4")

        self.report_type = ui.select(
            label="Reoprt Type", value="Bug", options=self.report_types, with_input=True
        ).props(props_select)
        self.description = ui.textarea("Description of the issue")
        self.steps_to_reproduce = ui.textarea(
            "Steps to reproduce the bug - leave empty if not applicable"
        )
        self.expected_behavior = ui.textarea(
            "Expected behavior - describe what the behavior should be"
        )

        ui.button("Submit Report", on_click=self.submit).props(props_button).classes(
            "mt-4"
        )

    def load_reports(self):

        if not os.path.isfile(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            self.reports = orjson.loads(f.read())
        return self.reports

    def save_report_to_file(self, report: list):
        self.load_reports()
        self.reports.append(report)

        with open(self.path, "w", encoding="utf-8") as f:
            f.write(orjson.dumps(self.reports, option=orjson.OPT_INDENT_2).decode())

    def build_report(
        self, report_type, description, steps_to_reproduce, expected_behavior
    ):
        report = {
            "type": report_type,
            "description": description,
            "steps_to_reproduce": steps_to_reproduce,
            "expected_behavior": expected_behavior,
            "status": "To Do",
        }
        return report
