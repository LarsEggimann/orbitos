#!/usr/bin/env python3

from multiprocessing.connection import Connection

import plotly.graph_objects as go  # type: ignore
from nicegui import ui
import logging
import os
import shutil
import time
from multiprocessing.connection import Connection
from pathlib import Path
import tempfile
from static.global_ui_props import *
import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry
from nicegui import ui

from util.settings_handler import SettingsHandler

wd = Path(__file__).parent
logger = logging.getLogger()

class MeteoComponent:
    def __init__(self):
        self.dark_mode: bool

        

        self.plot_temp = go.Figure(
            go.Scattergl(
                x=[0],
                y=[0],
                mode="lines",
            )
        ).update_layout(
            margin=dict(l=2, r=2, b=2, t=2, pad=2),
            dragmode="zoom",
            xaxis_title="Time [datetime]",
            yaxis_title="Temperature [C°]",
        )

        self.plot_temp_nicegui: ui.plotly
    
    async def load_temps(self):
        # Setup the Open-Meteo API client with cache and retry on error
        self.cache_session = requests_cache.CachedSession(Path(wd / '.weather_cache'), expire_after = 3600)
        self.retry_session = retry(self.cache_session, retries = 5, backoff_factor = 0.2)
        self.openmeteo = openmeteo_requests.Client(session = self.retry_session)

        # Make sure all required weather variables are listed here
        # The order of variables in hourly or daily is important to assign them correctly below
        self.url = "https://api.open-meteo.com/v1/forecast"
        self.params = {
            "latitude": 46.9481,
            "longitude": 7.4474,
            "hourly": "temperature_2m"
        }

        responses = self.openmeteo.weather_api(self.url, params=self.params)

        # Process first location. Add a for-loop for multiple locations or weather models
        response = responses[0]

        # Process hourly data. The order of variables needs to be the same as requested.
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}
        hourly_data["temperature_2m"] = hourly_temperature_2m

        self.hourly_dataframe = pd.DataFrame(data = hourly_data)

        self.plot_temp.update_traces(
            x=self.hourly_dataframe["date"],
            y=self.hourly_dataframe["temperature_2m"],
        )

        self.plot_temp_nicegui.update()

    @ui.refreshable
    def temp_plot(self):
        ui.timer(0.01, self.load_temps, once=True)
        self.plot_temp_nicegui = ui.plotly(self.plot_temp).classes("w-full h-96")

    
    @ui.refreshable
    def create_ui(self):
        resize = (
            ui.button()
            .on(
                "resize", lambda: self.temp_plot.refresh, throttle=0.05 # pylint: disable=no-member
            )
            .classes("hidden")
        )
        ui.add_head_html(
            f"""
        <script>
        function emitResizeEvent() {{
            content = document.querySelector('.nicegui-content');
            getElement({resize.id}).$emit('resize', content.offsetWidth);
        }}
        window.onload = emitResizeEvent;
        window.onresize = emitResizeEvent;
        </script>
        """
        )

        with ui.card().classes("w-full p-4"):
            with ui.row(wrap=False).classes("w-full items-center justify-between p-1"):

                ui.label("Temperature forecast in Bern")
                ui.link("Data from Open-Meteo", "https://open-meteo.com/", new_tab=True)
        
        self.temp_plot()


    def set_dark_mode(self, value: bool):
        self.dark_mode = value
        try:
            self.plot_temp.update_layout(
                go.Layout(template="plotly_dark" if value else "seaborn")
            )
            self.plot_temp_nicegui.update()
        except AttributeError:
            pass