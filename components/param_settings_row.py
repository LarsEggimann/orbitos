#!/usr/bin/env python3

from typing import Callable
from static.global_ui_props import props_input

from nicegui import ui


def create_param_settings_row(
    label_text: str,
    number_input_value: float,
    setting_on_change: Callable,
    validation_dict=None,
    slider_limits: tuple = (0, 1),
    slider_steps: float = 0.01,
    disable_checkbox: bool = True,
    checkbox_on_change: Callable = lambda: None,
) -> None:
    # def checkbox_on_change_local():
    #     if checkbox_on_change is not None:
    #         checkbox_on_change(ui_checkbox)
    #     set_enabled_status()

    # def set_enabled_status():
    #     ui_input.enabled = ui_checkbox.value
    #     ui_slider.enabled = ui_checkbox.value

    # ui_checkbox = (
    #     ui.checkbox(
    #         value=disable_checkbox,
    #         on_change=checkbox_on_change_local,
    #     )
    #     .on(
    #         "update:model-value",
    #         lambda e: ui.notify(
    #             f"Setting {label_text} "
    #             + ("enabled" if ui_checkbox.value else "disabled")
    #         ),
    #     )
    #     .classes("flex")
    # )

    def on_value_change(e):
        if e.args is None:
            return
        setting_on_change(e.args)
        ui.notify(f"{label_text} set to: {e.args}")

    ui.label(label_text)
    ui_input = (
        ui.number(
            value=number_input_value,
            validation=validation_dict,
            min=slider_limits[0],
            max=slider_limits[1],
        )
        .on(
            "update:model-value",
            on_value_change,
            throttle=0.5,
            leading_events=False,
        )
        .props(props_input)
    )
    ui_slider = (
        (ui.slider(min=slider_limits[0], max=slider_limits[1], step=slider_steps))
        .on(
            "update:model-value",
            on_value_change,
            throttle=1.0,
            leading_events=False,
        )
        .bind_value(ui_input, "value")
    )

    # if disable_checkbox:
    #     ui_checkbox.disable()

    # set_enabled_status()
