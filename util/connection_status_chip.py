#!/usr/bin/env python3

from nicegui import ui


class ConnectionStatusChip:
    def __init__(self, healthy):
        self.chip = ui.chip(text_color="white")
        self.connected_bool = False
        self.color = "negative"
        self.healthy = healthy
        self.update()

    def update(self):
        if self.healthy.value is True:
            self.chip.text = "Connected"
            self.color = "positive"
            self.connected_bool = True
        else:
            self.chip.text = "Not Connected"
            self.color = "negative"
            self.connected_bool = False

        self.chip.set_text(self.chip.text)
        self.chip.classes(replace=f"bg-{self.color}")
        self.chip.update()
