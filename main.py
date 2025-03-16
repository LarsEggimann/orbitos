#!/usr/bin/env python3

"""
Main module of ORBITOS.
"""

import logging
import os
import signal
import sys
from pathlib import Path
from components.meteo import MeteoComponent

from components import create_layout, device_manager
from components.bug_reports import BugReporter
from components.dose_calibration import DoseCalibration
from logs import setup_logging
from nicegui import Client, app, core, ui
from util.simple_auth import AuthMiddleware

working_directory = Path(__file__).parent
logger = logging.getLogger()


@ui.page("/chopper_wheel")
async def chopper_wheel_page():
    create_layout()
    show_logs_with(device_manager.chopper_wheel_ui)  # type: ignore


@ui.page("/electrometer1")
async def ion_chamber_page():
    create_layout()
    show_logs_with(device_manager.ion_chamber_ui)  # type: ignore

@ui.page("/electrometer2")
async def electrometer():
    create_layout()
    show_logs_with(device_manager.electrometer_ui)  # type: ignore

@ui.page("/electrometers")
async def electrometers():
    create_layout()
    show_logs_with(device_manager.electrometers_ui)  # type: ignore


@ui.page("/dose_calibration")
async def dose_calibration():
    dc = DoseCalibration()
    create_layout([dc])
    show_logs_with(dc.create_ui)


@ui.page("/stages")
async def combo_view():
    create_layout()
    show_logs_with(device_manager.stages_ui)  # type: ignore


@ui.page("/lab_notes")
async def notes():
    create_layout()

    def actual_ui():
        device_manager.lab_notes_ui()

    show_logs_with(actual_ui)

@ui.page("/flash")
async def flash():
    create_layout()

    def actual_ui():
        device_manager.flash_ui()

    show_logs_with(actual_ui)

@ui.page("/combined_data_view")
async def combined_dat_view():
    create_layout()

    def actual_ui():
        device_manager.combined_data_view_ui()

    show_logs_with(actual_ui)


@ui.page("/bug_reports")
async def bug_reports():
    create_layout()
    bug_reporter = BugReporter()

    def actual_ui():
        bug_reporter.create_ui()

    show_logs_with(actual_ui)

@ui.page("/meteo")
async def meteo():
    create_layout()
    meteo = MeteoComponent()
    show_logs_with(meteo.create_ui)  # type: ignore


@ui.page("/main")
async def main():
    """
    Entry point of the program.
    Initializes ORBITOS and sets up the user interface.
    """
    create_layout()

    def actual_ui():
        with ui.row(wrap=False).classes("w-full items-center"):

            with ui.element().classes("w-2/3 h-full col-span-2 items-center"):
                with ui.card().classes("mb-2 w-full grow items-center"):
                    ui.label("Welcome to ORBITOS!")

                    ui.label(
                        "More detailed settings and controls will be available in the side drawer under the respective component."
                    )
                

            with ui.card().classes("w-1/3 items-center"):
                image_path = working_directory / "static" / "flash_setup.jpg"
                ui.image(source=image_path).classes("w-full h-auto")



        with ui.card().classes("w-full p-4"):
            device_manager.create_device_manager_ui()

    show_logs_with(actual_ui)


def show_logs_with(actual_ui):
    if app.storage.user.get("show-with-logs", False):

        path = working_directory / "logs" / "logs.log"

        class Logs:
            value = ""

        logs = Logs()

        def read_logs():
            nonlocal logs
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    logs.value = f.readlines()[-50:]
                    logs.value = "".join(logs.value)

        ui.timer(1, read_logs)

        with ui.splitter(value=60).classes("w-full") as splitter:
            with splitter.before:
                actual_ui()
            with splitter.after:
                with ui.element().classes("w-full h-full"):
                    area = (
                        ui.code(language="")
                        .bind_content_from(logs, "value")
                        .classes("w-full h-full")
                    )
    else:
        actual_ui()


def handle_sigint(signum, frame) -> None:
    # `disconnect` is async, so it must be called from the event loop; we use `ui.timer` to do so.
    ui.timer(0.1, disconnect, once=True)
    # Delay the default handler to allow the disconnect to complete.
    ui.timer(1, lambda: signal.default_int_handler(signum, frame), once=True)


async def disconnect() -> None:
    """Disconnect all clients from current running server."""
    for client_id in Client.instances:
        await core.sio.disconnect(client_id)


async def cleanup():
    logger.info("Exiting ORBITOS application ...")
    device_manager.reset_connections()
    await disconnect()


if __name__ in {"__main__", "__mp_main__"}:

    setup_logging()

    app.add_middleware(AuthMiddleware)
    app.on_shutdown(cleanup)
    signal.signal(signal.SIGINT, handle_sigint)

    ui.navigate.to("/main")
    try:
        args = sys.argv[1]
    except IndexError:
        args = "--dev-mode"

    if args == "--lab-mode":
        reload = False
        show = True
    else:
        reload = True
        show = False

    logger.info(f'Starting ORBITOS in "{args}" mode.')

    def on_start():
        urls = " http://localhost:50050, http://192.168.113.7:50050"
        logger.info(f"ORBITOS ready to go on: {urls}")

    app.on_startup(on_start)

    ui.run(
        reload=reload,
        show=show,
        on_air=None,
        binding_refresh_interval=0.1,
        host="0.0.0.0",
        title="ORBITOS",
        favicon=str(working_directory / "static" / "icon.ico"),
        port=50050,
        show_welcome_message=False,
        storage_secret="flash-control-panel",
    )
