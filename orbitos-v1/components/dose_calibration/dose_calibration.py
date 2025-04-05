#!/usr/bin/env python3

import logging
from pathlib import Path

import numpy as np  # type: ignore
import pandas as pd  # type: ignore
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
from skimage import io
from nicegui import events, ui, app
from static.global_ui_props import *
import asyncio

logger = logging.getLogger()
work_dir = Path(__file__).parent


def float_if_present(value):
    if value:
        return float(value)
    return None


class DoseCalibration:
    def __init__(self):

        self.manual_circle_radius: float = None  # type: ignore
        self.max_expected_dose: float = 20

        self.film_calibration_data = self.define_film_calibration_data()
        self.selected_film_calibration = self.film_calibration_data[
            "EBT3_new_METAS_ImageJwRGB"
        ]

        self.foil_image = io.imread(work_dir / "example_scan.tif")
        self.create_plotly_image_view()

        self.selection_center: tuple[float, float] = (
            self.foil_image.shape[1] / 2,
            self.foil_image.shape[0] / 2,
        )
        self.selection_radius: float = 100

        self.ui_image_view: ui.plotly

        self.plotly_dose_heatmap = go.Figure().update_layout(
            font_family="'Oswald', sans-serif"
        )
        self.ui_dose_heatmap: ui.plotly

        self.plotly_horizontal_profile = go.Figure()
        self.ui_horizontal_profile: ui.plotly

        self.mean_dose: float = None
        self.std_dose: float = None

        self.calculated_dose_rate: float = None
        self.time_spent_in_slit_per_pixel: float = None

        self.used_chopper_wheel: bool = True
        self.chopper_wheel_speed: float = 0.1
        self.number_of_rotations: int = 1

        self.calculate_dose_of_circle()

    def create_plotly_image_view(self):
        self.plotly_image_view = px.imshow(self.foil_image).update_layout(
            go.Layout(
                margin=dict(l=2, r=2, b=2, t=2, pad=2),
                dragmode="drawcircle",
                modebar=dict(add=["drawcircle", "eraseshape"]),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
        )

    def upload_file(self, e: events.UploadEventArguments):
        self.foil_image = io.imread(e.content)
        # clear the plotly image view
        self.plotly_image_view.data = []
        self.create_plotly_image_view()
        self.scan_image_plot.refresh()  # pylint: disable=no-member

    def erase_drawed_shapes(self):
        self.plotly_image_view.data = [self.plotly_image_view.data[0]]
        self.selection_center = None
        self.scan_image_plot.refresh()  # pylint: disable=no-member

    def on_lasso_draw(self, e: events.GenericEventArguments):
        keys = e.args.keys()
        if "shapes" in keys:
            last_shape = e.args["shapes"][-1]
            if "type" in last_shape and last_shape["type"] == "circle":
                p1 = last_shape["x0"], last_shape["y0"]
                p2 = last_shape["x1"], last_shape["y1"]
                self.selection_center = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
                radius_in_x = abs(p2[0] - self.selection_center[0])
                radius_in_y = abs(p2[1] - self.selection_center[1])
                self.selection_radius = np.mean([radius_in_x, radius_in_y])
                center_string = (
                    f"{self.selection_center[0]:.2f}, {self.selection_center[1]:.2f}"
                )
                self.log_and_notify(
                    f"Circle drawn at {center_string} with radius {self.selection_radius:.2f}"
                )

    def calculate_dose_of_circle(self):
        if self.selection_center is None:
            self.log_and_notify("Please draw a circle first")
            return

        if self.manual_circle_radius:
            self.selection_radius = self.manual_circle_radius

        pixel_coords, pixel_values = self.mask_circle(
            np.array(self.foil_image), self.selection_center, self.selection_radius
        )
        dose_values = self.inv_green_saunders(
            pixel_values, *self.selected_film_calibration["pars"]
        )
        self.create_heatmap_and_horizontal_profile(pixel_coords, dose_values)

        self.calculate_dose_rate_stuff()

    def set_dark_mode(self, value: bool):
        self.dark_mode = value
        try:
            template = "plotly_dark" if value else "seaborn"

            self.plotly_dose_heatmap.update_layout(template=template)
            self.ui_dose_heatmap.update()

            self.plotly_horizontal_profile.update_layout(template=template)
            self.ui_horizontal_profile.update()

            self.ui_image_view.update()

        except AttributeError as e:
            logger.error(e)

    @ui.refreshable
    def scan_image_plot(self) -> ui.plotly:
        self.ui_image_view = (
            ui.plotly(self.plotly_image_view)
            .on("plotly_relayout", self.on_lasso_draw)
            .classes("w-full")
        )
        self.ui_image_view._props["options"]["config"] = {"displaylogo": False}
        return self.ui_image_view

    @ui.refreshable
    def dose_heatmap_plot(self):
        template = "plotly_dark" if app.storage.user["dark-mode"] else "seaborn"
        self.plotly_dose_heatmap.update_layout(template=template)
        self.ui_dose_heatmap = ui.plotly(self.plotly_dose_heatmap)

    @ui.refreshable
    def horizontal_profile_plot(self):
        template = "plotly_dark" if app.storage.user["dark-mode"] else "seaborn"
        self.plotly_horizontal_profile.update_layout(template=template)
        self.ui_horizontal_profile = ui.plotly(self.plotly_horizontal_profile)
        ui.button(
            "Download Data",
            icon="download",
            on_click=self.download_horizontal_profile_plot_data,
        ).classes("m-2").props(props_button)

    def create_ui(self):

        with ui.splitter(on_change=self.on_change_refresh).classes(
            "w-full"
        ) as splitter:
            with splitter.before:
                with ui.element().classes("w-full p-1"):

                    with ui.card().classes("w-full mb-2"):
                        with ui.expansion(
                            text="Upload film scan",
                            caption="Upload scan of irradiated film and draw circle to select area of interest",
                            icon="upload",
                            value=False,
                            on_value_change=self.scan_image_plot.refresh, # pylint: disable=no-member
                        ).classes(
                            "w-full"
                        ):
                            with ui.element().classes("flex w-full"):
                                with ui.row(wrap=False).classes("flex w-full"):
                                    self.scan_image_plot()
                                    with ui.element().classes("flex w-40"):
                                        ui.upload(
                                            label="Uploader",
                                            auto_upload=True,
                                            multiple=False,
                                            on_upload=self.upload_file,
                                        ).props("accept=.tif").classes("m-1 w-40")
                                        ui.button(
                                            text="Reset Drawings",
                                            icon="delete",
                                            on_click=self.erase_drawed_shapes,
                                        ).classes("m-1").props(props_button)

                    with ui.card().classes("w-full mb-2"):
                        with ui.expansion(
                            text="Dose calibration Settings",
                            caption="Select calibration data and adjust boundary conditions",
                            icon="tune",
                            value=False,
                        ).classes("w-full"):

                            with ui.row(wrap=False).classes("flex w-full "):
                                ui.input(label="Max expected dose").bind_value(
                                    self, "max_expected_dose", forward=float_if_present
                                ).classes("w-1/2").props(props_input)
                                ui.input(label="Manual circle radius").bind_value(
                                    self,
                                    "manual_circle_radius",
                                    forward=float_if_present,
                                ).classes("w-1/2").props(props_input)

                            def select_film_calibration(
                                e: events.ValueChangeEventArguments,
                            ):
                                self.selected_film_calibration = (
                                    self.film_calibration_data[e.value]
                                )
                                self.log_and_notify(
                                    f"Selected film calibration: {self.selected_film_calibration['calib_str']}"
                                )

                            with ui.row(wrap=False).classes("flex w-full m-2"):
                                ui.select(
                                    value="EBT3_new_METAS_ImageJwRGB",
                                    label="Film calibration data",
                                    options=list(self.film_calibration_data.keys()),
                                    on_change=select_film_calibration,
                                ).props(props_select)
                                ui.label().bind_text_from(
                                    self,
                                    "selected_film_calibration",
                                    backward=lambda x: x["calib_str"],
                                )

                    with ui.card().classes("w-full mb-2"):
                        with ui.expansion(
                            text="Dose Rate calculation settings",
                            caption="Adjust settings regarding the calculation of the Dose Rate",
                            icon="history",
                            value=False,
                        ).classes("w-full"):
                            ui.switch(
                                "Used the chopper Wheel for the irradiation?",
                                value=self.used_chopper_wheel,
                            ).bind_value(self, "used_chopper_wheel")
                            ui.label(
                                "Using chopper wheel geometry and speed we can calculate the doserate:"
                            )
                            ui.input(
                                label="Chopper wheel speed (rps)",
                                value=self.chopper_wheel_speed,
                                on_change=self.calculate_dose_rate_stuff,
                            ).bind_value_to(
                                self, "chopper_wheel_speed", forward=float_if_present
                            ).bind_enabled_from(
                                self, "used_chopper_wheel"
                            ).classes(
                                "w-1/2"
                            ).props(
                                props_input
                            )
                            ui.input(
                                label="Number of rotations",
                                value=self.number_of_rotations,
                                on_change=self.calculate_dose_rate_stuff,
                            ).bind_value_to(
                                self, "number_of_rotations", forward=int
                            ).bind_enabled_from(
                                self, "used_chopper_wheel"
                            ).classes(
                                "w-1/2"
                            ).props(
                                props_input
                            )
                            ui.label().bind_text_from(
                                self,
                                "time_spent_in_slit_per_pixel",
                                backward=lambda x: f"Time spent in slit per pixel: {x} s",
                            ).bind_visibility_from(self, "used_chopper_wheel")
                            ui.input(
                                label="Estimated irradiation time per pixel",
                                value=self.time_spent_in_slit_per_pixel,
                            ).bind_value_to(
                                self,
                                "time_spent_in_slit_per_pixel",
                                forward=float_if_present,
                            ).bind_visibility_from(
                                self, "used_chopper_wheel", backward=lambda x: not x
                            ).classes(
                                "w-1/2"
                            ).props(
                                props_input
                            )

                            def calc_time(e: events.ValueChangeEventArguments):
                                if (
                                    self.calculated_dose_rate
                                    and self.chopper_wheel_speed > 0
                                ):
                                    return f"Time taken to irradiate with Chopper Wheel: {(self.number_of_rotations + 0.8) / self.chopper_wheel_speed} s"

                            ui.label().bind_text_from(
                                self, "time_spent_in_slit_per_pixel", backward=calc_time
                            ).bind_visibility_from(self, "used_chopper_wheel")
                            ui.label().bind_text_from(
                                self,
                                "calculated_dose_rate",
                                backward=lambda x: f"Calculated dose rate: {x} Gy/s",
                            )

                    with ui.card().classes("w-full mb-2"):
                        ui.button(
                            "Do It!",
                            icon="calculate",
                            on_click=self.calculate_dose_of_circle,
                        ).props(props_button)

            with splitter.after:
                with ui.element().classes("w-full p-2"):
                    self.dose_heatmap_plot()
                    self.horizontal_profile_plot()

    def calculate_dose_rate_stuff(self):
        # dose rate from chopper wheel geometry
        slit_width = 1.308 + 0.91  # /2 *2 for full width from drawing
        circumference = 2 * np.pi * 85  # 85mm radius at middle of slit
        slit_angle = (slit_width / circumference) * 360  # in degrees
        if self.used_chopper_wheel and self.chopper_wheel_speed > 0:
            self.time_spent_in_slit_per_pixel = (
                slit_angle / (360 * self.chopper_wheel_speed)
            ) * self.number_of_rotations  # in seconds
        self.calculated_dose_rate = self.mean_dose / self.time_spent_in_slit_per_pixel

    def create_heatmap_and_horizontal_profile(self, circle_coords, circle_pixels):
        center_x, center_y = self.selection_center
        radius = self.selection_radius

        dpi = 400

        # Find the minimum and maximum coordinates of the circle within the larger image
        min_x, min_y = int(center_x - radius), int(center_y - radius)
        max_x, max_y = int(center_x + radius), int(center_y + radius)

        # Create a heatmap using the pixel values
        heatmap = np.zeros((max_y - min_y + 1, max_x - min_x + 1))
        for coords, value in zip(circle_coords, circle_pixels):
            y, x = coords
            if min_x < x < max_x and min_y < y < max_y:
                if value < self.max_expected_dose:
                    heatmap[y - min_y - 1, x - min_x - 1] = value
                else:
                    heatmap[y - min_y - 1, x - min_x - 1] = 0

        # Convert pixel positions to mm positions
        x_ticks_mm = np.linspace(
            min_x / dpi * 25.4, max_x / dpi * 25.4, heatmap.shape[1]
        )
        y_ticks_mm = np.linspace(
            min_y / dpi * 25.4, max_y / dpi * 25.4, heatmap.shape[0]
        )

        # Calculate mean and standard deviation of non-zero values in the heatmap
        non_zero_values = heatmap[heatmap != 0]
        self.mean_dose = np.mean(non_zero_values)
        self.std_dose = np.std(non_zero_values)
        error_in_percent = self.std_dose / self.mean_dose * 100

        logger.info(
            f"Mean: {self.mean_dose:.5f} Gy, error: {self.std_dose:.5f}, error in percent: {error_in_percent:.3f}%"
        )

        # Create the heatmap plot
        self.plotly_dose_heatmap = (
            go.Figure(
                data=go.Heatmap(
                    z=heatmap,
                    x=x_ticks_mm,
                    y=y_ticks_mm,
                    colorscale="viridis",
                    colorbar=dict(title="Dose (Gy)"),
                )
            )
            .update_yaxes(autorange="reversed")
            .update_layout(
                title=f"Dose Heatmap - Mean Value: {self.mean_dose:.2f} ± {self.std_dose:.2f} Gy (error in percent: {error_in_percent:.2f}%)",
                xaxis_title="x [mm]",
                yaxis_title="y [mm]",
                margin=dict(l=40, r=40, t=40, b=40),
            )
        )
        self.dose_heatmap_plot.refresh()  # pylint: disable=no-member

        profile_along_middle = heatmap[heatmap.shape[0] // 2, :]
        # delete zero values
        profile_along_middle = profile_along_middle[profile_along_middle != 0]

        self.plotly_horizontal_profile = go.Figure(
            go.Scatter(
                x=x_ticks_mm,
                y=profile_along_middle,
                mode="lines",
            )
        ).update_layout(
            title="Horizontal Profile",
            xaxis_title="x [mm]",
            yaxis_title="Dose [Gy]",
            margin=dict(l=40, r=40, t=40, b=40),
        )
        self.horizontal_profile_plot.refresh()  # pylint: disable=no-member

    async def download_horizontal_profile_plot_data(self):
        # Download the data of the heatmap and the horizontal profile as dataframes
        x_ticks_mm = self.plotly_dose_heatmap.data[0].x
        y_ticks_mm = self.plotly_dose_heatmap.data[0].y
        z = self.plotly_dose_heatmap.data[0].z
        df_heatmap = pd.DataFrame(z, columns=x_ticks_mm, index=y_ticks_mm)

        x = self.plotly_horizontal_profile.data[0].x
        y = self.plotly_horizontal_profile.data[0].y
        df_profile = pd.DataFrame({"x [mm]": x, "Dose [Gy]": y})

        d_path = Path(work_dir / "dose_heatmap.csv")
        p_path = Path(work_dir / "horizontal_profile.csv")

        # Save the dataframes as CSV files
        df_heatmap.to_csv(d_path)
        df_profile.to_csv(p_path)

        ui.download(d_path, "dose_heatmap_data")
        ui.download(p_path, "horizontal_profile_data")

        await asyncio.sleep(1)

        # Remove the CSV files
        d_path.unlink()
        p_path.unlink()

    def on_change_refresh(self):
        self.scan_image_plot.refresh()  # pylint: disable=no-member
        self.dose_heatmap_plot.refresh()  # pylint: disable=no-member
        self.horizontal_profile_plot.refresh()  # pylint: disable=no-member

    def mask_circle(self, image_np_rgb, center, radius):
        center_x, center_y = center
        image_gray = np.dot(image_np_rgb[..., :3], [0.2989, 0.5870, 0.1140])
        # Create a grid of pixel coordinates
        height, width = image_gray.shape
        X, Y = np.meshgrid(np.arange(width), np.arange(height))
        # Calculate squared distance from each pixel to the circle center
        squared_distance = (X - center_x) ** 2 + (Y - center_y) ** 2
        # Use the squared distance to create a mask for pixels within the circle
        mask = squared_distance <= radius**2
        # Use the mask to extract the pixels within the circle
        circle_pixels = image_gray[mask]
        circle_coords = np.column_stack((Y[mask], X[mask]))
        return circle_coords, circle_pixels

    def log_and_notify(self, message: str):
        logger.info(message)
        ui.notify(message)

    def green_saunders(self, dose, Do, PVmin, PVmax, beta):
        return np.where(
            dose == 0, 1e20, PVmin + (PVmax - PVmin) / (1 + (Do / dose) ** beta)
        )

    def inv_green_saunders(self, pixel_value, Do, PVmin, PVmax, beta):
        val = Do * ((pixel_value - PVmin) / (PVmax - pixel_value)) ** (1 / beta)
        return np.nan_to_num(val)

    def define_film_calibration_data(self):
        return {
            "EBT3_old_Bologna": {
                "pars": np.array([4.7956, 45.5929, 159.0524, -0.9054]),
                "calib_str": "\tOld EBT-3\n\tExp. 02.03.2023\n\tLot 030220102\n\tCalibration at Bologna with GammaCell\n\tdd.mm.2023",
            },
            "EBT3_new_Linac_ImageJ": {
                "pars": np.array([5.62, 16.82, 159.27, -0.86]),
                "calib_str": "\tNew EBT-3\n\tExp. 02.10.2024\n\tLot 10032202\n\tCalibration at Inselspital with Clinical Linac (ImageJ non-weighted Pixel Values)\n\t25.09.2023",
            },
            "EBT3_new_Linac_Py": {
                "pars": np.array([4.99, 11.73, 168.79, -0.88]),
                "calib_str": "\tNew EBT-3\n\tExp. 02.10.2024\n\tLot 10032202\n\tCalibration at Inselspital with Clinical Linac (Python weighted Pixel Values)\n\t25.09.2023",
            },
            "EBT3_new_METAS_ImageJwRGB": {
                "pars": np.array([5.19, 8.40, 167.13, -0.87]),
                "calib_str": "\tNew EBT-3\n\tExp. 02.10.2024\n\tLot 10032202\n\tCalibration at METAS with 60-Co source (ImageJ weighted Pixel Values)\n\t07.11.2023",
            },
            "EBT3_old_METAS_ImageJwRGB": {
                "pars": np.array([5.22, 16.46, 155.37, -0.87]),
                "calib_str": "\tOld EBT-3\n\tExp. 02.03.2023\n\tLot 030220102\n\tCalibration at METAS with 60-Co source (ImageJ weighted Pixel Values)\n\t07.11.2023",
            },
            "EBT3_new_combinedLiMet_ImageJwRGB": {
                "pars": np.array([5.09, 10.13, 167.96, -0.88]),
                "calib_str": "\tNew EBT-3\n\tExp. 02.10.2024\n\tLot 10032202\n\tFitted to METAS and Linac data combined (ImageJ weighted Pixel Values)\n\t15.11.2023",
            },
            "HDV2": {
                "pars": np.array([144.58, 47.81, 211.03, -0.85]),
                "calib_str": "\tNew HD-V2\n\tExp. __\n\tLot ___\n\tCalibration at ISOF Bologna with GammaCell (ImageJ weighted Pixel Values)\n\t19.12.2023",
            },
            "EBT3_hzdrE3_3FN_24h": {
                "pars": np.array([1.74, 4.10, 168.40, -0.83]),
                "calib_str": '\tEBT3\n\tExp. 02.10.2024\n\tLot 10032202\n Calibration at HZDR 8 MeV protons 24h scanning time \n\t08.02.2025',
            },
        }
