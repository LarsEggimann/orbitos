#!/usr/bin/env python3

import logging
from pathlib import Path
from nicegui import ui
import pandas as pd # type: ignore
import plotly.graph_objects as go # type: ignore
from static.global_ui_props import *
from util.connection_manager_base import ConnectionManagerBase
from datetime import datetime



logger = logging.getLogger()
work_dir = Path(__file__).parent


class CombinedDataView:
    def __init__(self, connection_managers: list[ConnectionManagerBase]) -> None:
        # remove the stages connection manager
        self.connection_managers = connection_managers
        self.connection_managers_dict = dict()
        for m in self.connection_managers:
            self.connection_managers_dict[m] = m.name

        self.selected_c_managers: list[ConnectionManagerBase] = []

        self.em_data1: pd.DataFrame = None
        self.em_data2: pd.DataFrame = None
        self.cw_data: pd.DataFrame = None

        self.plot_plotly: go.Figure = go.Figure()
        self.plot_nicegui: ui.plotly = None # type: ignore
 
    
    def reset_datasources(self):
        self.selected_c_managers.clear()
        self.em_data1 = None
        self.em_data2 = None
        self.cw_data = None
        self.create_ui.refresh() # pylint: disable=no-member
        self.create_plot_ui.refresh() # pylint: disable=no-member

    @ui.refreshable
    def create_ui(self):
        with ui.card().classes("w-full mb-2"):
            with ui.row(wrap=False).classes("w-full items-center flex p-1"):

                with ui.row(wrap=False).classes("m-1 p-4 w-full items-center"):
                    ui.label("Combined Data View - select datasources").style("font-size: 20px; font-weight: bold;")
                    ui.button("Update Plot", on_click=self.update_plot_and_data, color="positive").classes("m-1").props(props_button + " outline")

                ui.space()

                def callback(e):
                    if e.value in self.selected_c_managers:
                        ui.notify(f"Datasource {e.value.name} already selected", type="warning", position="top", multi_line=True)
                    else:
                        self.selected_c_managers = e.value
                    self.create_plot_ui.refresh() # pylint: disable=no-member
                    
                with ui.row(wrap=False).classes("m-1 p-4 w-full items-center"):
                    ui.label("To add a datasource, select from the dropdown:").style("font-size: 14px; font-weight: bold;")
                    ui.select(options=self.connection_managers_dict, multiple=True, label="Datasource", on_change=callback, value=self.selected_c_managers).props(props_select + ' use-chips').classes("w-64").tooltip("Note that more than 2 components can lead to visual clutter and clipping in the ui ...")

                ui.button("Reset Datasources", on_click=self.reset_datasources).classes("m-1").props(props_button)

        self.create_plot_ui()


    @ui.refreshable
    def create_plot_ui(self):
        with ui.card().classes("w-full mb-2"):
            self.plot_nicegui = ui.plotly(self.get_plotly_plot()).classes("w-full h-96")


    async def update_plot_and_data(self):
        plot = self.get_plotly_plot()
        self.plot_nicegui.update_figure(plot)

    def get_plotly_plot(self):

        self.em_data1 = None
        self.em_data2 = None
        self.cw_data = None

        for m in self.selected_c_managers:
            match m.name:
                case "Electrometer 1": self.em_data1 = pd.read_csv(m.data_file_handler.full_filename)
                case "Electrometer 2": self.em_data2 = pd.read_csv(m.data_file_handler.full_filename)
                case "Chopper Wheel": self.cw_data = pd.read_csv(m.data_file_handler.full_filename)

        self.plot_plotly = go.Figure()

        if self.em_data1 is not None:
            self.em_data1['time'] = [datetime.fromtimestamp(x) for x in self.em_data1['time']]

            self.plot_plotly.add_trace(go.Scatter(x=self.em_data1['time'], y=self.em_data1['current'], mode='lines', name='em 1 data'))
            self.plot_plotly.update_layout(yaxis=dict(title='current [A]', autoshift=True, anchor='free',))

        if self.em_data2 is not None:
            self.em_data2['time'] = [datetime.fromtimestamp(x) for x in self.em_data2['time']]

            self.plot_plotly.add_trace(go.Scatter(x=self.em_data2['time'], y=self.em_data2['current'], mode='lines', name='em 2 data'))


        if self.cw_data is not None:
            self.cw_data['timestamp'] = [datetime.fromtimestamp(x) for x in self.cw_data['timestamp']]
            self.plot_plotly.add_trace(go.Scatter(x=self.cw_data['timestamp'], y=self.cw_data['angular_position'], mode='lines', name='cw angular position', yaxis='y3'))
            self.plot_plotly.add_trace(go.Scatter(x=self.cw_data['timestamp'], y=self.cw_data['velocity'], mode='lines', name='cw velocity', yaxis='y4'))
            self.plot_plotly.update_layout(
                yaxis3=dict(title='angular position [°]', overlaying='y', side='right', autoshift=True, anchor='free', showgrid=False),
                yaxis4=dict(title='velocity [rps]', overlaying='y', side='right', autoshift=True, anchor='free', shift=20, showgrid=False),
            )
        self.plot_plotly.update_layout(
            xaxis=dict(rangeslider_visible=True),
            )
        # decrease the margins
        self.plot_plotly.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            template='plotly_white'
        )
        return self.plot_plotly
    
    def set_dark_mode(self, value: bool):
        if value:
            self.plot_plotly.update_layout(template='plotly_dark')
        else:
            self.plot_plotly.update_layout(template='plotly_white')

        if self.plot_nicegui is not None:
            self.plot_nicegui.update()

    
    def log_and_notify(self, message: str):
        logger.info(message)
        ui.notify(message)