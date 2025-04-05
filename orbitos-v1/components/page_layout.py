#!/usr/bin/env python3
import asyncio
import logging
import logging.config
from pathlib import Path
from components import device_manager
from nicegui import app, run, ui
from util.simple_auth import logout_buttons
from static.global_ui_props import *
import os

logger = logging.getLogger()
working_directory = Path(__file__).parent.parent

media_directory = Path(working_directory / "static")
app.add_media_files("/audio", local_directory=media_directory)


def create_layout(further_components=[]):

    # apply css styles
    ui.add_head_html(
        "<style>"
        + open(working_directory / "static" / "styles.css", encoding="utf-8").read()
        + "</style>"
    )

    def select_palette(primary_override=None):
        value = app.storage.user.get("color-palette", "default")
        theme = colors[value]
        if primary_override:
            primary = primary_override
        else:
            primary = theme["primary"]
        ui.colors(
            primary=primary,
            secondary=theme["secondary"],
            accent=theme["accent"],
            dark=theme["dark"],
            positive=theme["positive"],
            negative=theme["negative"],
            info=theme["info"],
            warning=theme["warning"],
        )
        logger.debug("Palette updated to %s", value)

    def select_palette_button(value):
        app.storage.user["color-palette"] = value
        select_palette()
        app.storage.user.pop("primary-color", None)

    def reset_primary_color():
        app.storage.user.pop("primary-color", None)
        app.storage.user["color-palette"] = "default"
        select_palette()
        logger.info("Primary color reset")

    def update_primary_color(e):
        select_palette(e.color)
        app.storage.user["primary-color"] = e.color
        logger.info("Primary color updated")

    def set_dark_mode():
        value = app.storage.user.get("dark-mode", False)
        ui_dark_mode.value = value
        asyncio.create_task(run.io_bound(device_manager.set_dark_mode, value))  # type: ignore
        for component in further_components:
            asyncio.create_task(run.io_bound(component.set_dark_mode, value))  # type: ignore
        logger.debug("Dark mode toggled to %s", value)

    if "primary-color" in app.storage.user:
        select_palette(app.storage.user["primary-color"])
    else:
        select_palette()

    ui_dark_mode = ui.dark_mode()
    set_dark_mode()

    with ui.left_drawer(value=False).props("bordered") as left_drawer:
        ui.label("Navigation")

        ui.separator()

        ui.link("Main", "/main")

        ui.separator()

        ui.link("Flash UI", "/flash")

        ui.separator()

        ui.link("Chopper Wheel", "/chopper_wheel")

        ui.separator()

        ui.link("Electrometer 1", "/electrometer1")

        ui.separator()

        ui.link("Electrometer 2", "/electrometer2")

        ui.separator()

        ui.link("Electrometer 1 & 2", "/electrometers")

        ui.separator()

        ui.link("Stages", "/stages")

        ui.separator()

        ui.link("Combined Data View", "/combined_data_view")

        ui.separator()

        ui.link("Dose Calibration", "/dose_calibration")

        ui.separator()

        ui.link("Lab Notes", "/lab_notes")

        ui.separator()

        ui.link("Report a Bug or Request a feature", "/bug_reports")

        ui.space()

        ui.separator()

        ui.link("Weather?", "/meteo")

    with ui.right_drawer(value=False).props("bordered width=450") as right_drawer:
        ui.label("Settings")

        ui.switch(
            "Something is not right! - Show with logs.",
            value=app.storage.user.get("show-with-logs", False),
            on_change=lambda: ui.run_javascript("location.reload();"),
        ).bind_value(app.storage.user, "show-with-logs")
        ui.separator()

        with ui.expansion("Device Connections", icon="lan", value=False).classes(
            "w-full justify-items-center"
        ):
            device_manager.create_device_manager_ui()

        ui.separator()

        with ui.expansion("Appearance", icon="palette").classes(
            "w-full justify-items-center"
        ):
            ui.switch(
                "Dark Mode",
                on_change=set_dark_mode,
                value=app.storage.user.get("dark-mode", False),
            ).bind_value(app.storage.user, "dark-mode")

            ui.separator()

            with ui.row().classes("w-full items-center"):
                ui.label("Select Theme:")
                ui.select(
                    options=["default", "default2"],
                    value=app.storage.user.get("color-palette", "default"),
                    on_change=lambda e: select_palette_button(e.value),
                ).props(props_select)

            ui.separator()

            with ui.row().classes("w-full no-wrap justify-center items-center"):
                ui.label("Manually select primary color:")
                with ui.button(icon="colorize"):
                    ui.color_picker(on_pick=update_primary_color)
                ui.button(icon="refresh", on_click=reset_primary_color).tooltip(
                    "Reset primary color"
                )

        ui.separator()

        with ui.expansion("User", icon="manage_accounts").classes(
            "w-full justify-items-center"
        ):
            logout_buttons()

        path = working_directory / "main.py"
        relaunch_script = working_directory / "win_relaunch_script.bat"

        def hard_restart():

            def confirm_hard_restart():
                command = '"' + str(relaunch_script) + '"'
                os.system(command)
                dialog.close()

            with ui.dialog() as dialog, ui.card():
                ui.label("Are you sure you want to hard reset the software? This will kill all python processes currently running on the server.")
                with ui.row().classes("w-full justify-center items-center"):
                    ui.button("Yes, send it!", on_click=confirm_hard_restart).props(
                        props_button
                    )
                    ui.button("No, maybe it works now!", on_click=dialog.close).props(
                        props_button
                    )
            dialog.open()
            

        # ui.button('Restart ORBITOS', on_click=lambda: os.utime(str(path))).props(props_button)
        ui.button("Hard Restart ORBITOS", on_click=hard_restart).props(
            props_button
        )

    with ui.header(elevated=False).classes("flex justify-between"):
        ui.button(on_click=left_drawer.toggle, icon="menu").props("flat color=white")
        
        with ui.link(target="/main").tooltip("Go Home!"):
            ui.button(text="ORBITOS").props("flat color=white").classes("text-xl")

        ui.button(on_click=right_drawer.toggle, icon="settings").props(
            "flat color=white"
        )

    with ui.footer().classes("flex justify-between "):

        ui.label("ORBITOS - Omnipurpose Radiation Beam Instrumentation and Tuning Operational Software")

        times_clicked = 0

        def mysterious_button():
            audio.update()
            nonlocal times_clicked
            times_clicked += 1
            if times_clicked > 2:
                # audio.seek(103)
                audio.play()
                audio.props("controls")
                ui.notify("You found an easter egg! 🥚")

        with ui.row().classes("items-center"):
            ui.label("Made with")
            audio = ui.audio(src=str("audio/waiting.mp3"), controls=False)
            ui.button(" ❤️ ", on_click=mysterious_button, color=None).tooltip(
                "Whats this?"
            )
            ui.label("by Lars Eggimann")
            with ui.link(
                target="mailto:lars.eggimann@students.unibe.ch?subject=ORBITOS%20-%20Contact%20me%20Button&body=Hello%20there%20you%20kind%20creator%20of%20this%20magnificent%20app!%0A%0AI%20have%20found%20the%20following%20bug%3A",
                new_tab=True,
            ).tooltip("Contact Me!"):
                ui.icon("mail")
