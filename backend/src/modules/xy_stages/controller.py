import logging
import time
import threading

from sqlmodel import Session

from src.shared.websocket_manager import WebSocketManager
from src.shared.settings_manager import SettingsManager
from src.shared.state_manager import StateManager
from src.modules.xy_stages.models import (
    XY,
    XYStagesData,
    XYStagesDataResponse,
    XYStagesSettings,
    XYStagesSettingsSet,
    XYStagesState,
    XYStagesStatus,
)
from src.shared.models import ConnectionStatus
from src.modules.xy_stages.arcus_performax_stage import ArcusPerformaxStage
from src.core.db import engine

logger = logging.getLogger()

class XYStagesController:
    def __init__(
        self,
        device_name: str,
        ws_manager: WebSocketManager[XYStagesState, XYStagesDataResponse, XYStagesSettings],
    ):
        logger.info("Initializing xy stages wheel controller")

        self.device_name = device_name
        self.ws_manager = ws_manager

        self.settings: SettingsManager[XYStagesSettings] = SettingsManager(
            model=XYStagesSettings,
            device_id=1,  # hardcoded for xy stages since we consider it as one device
            device_name=self.device_name,
            engine=engine,
            on_settings_update=self.ws_manager.broadcast_setting_sync,
        )

        self.state: StateManager[XYStagesState] = StateManager(
            model=XYStagesState,
            device_name=self.device_name,
            on_state_update=self.ws_manager.broadcast_state_sync,
        )

        self._acquire_data_thread: threading.Thread | None = None
        self._acquire_data_event: threading.Event = threading.Event()

        self.xy_stages: dict[XY, ArcusPerformaxStage] = {
            XY.X_AXIS: ArcusPerformaxStage(name=XY.X_AXIS.value),
            XY.Y_AXIS: ArcusPerformaxStage(name=XY.Y_AXIS.value),
        }

    def connect(self, axis: XY,  index: int) -> None:
        logger.info("Connecting to xy stage %s on at index %s", axis.value, index)

        if self.xy_stages[axis].state.connection_status == ConnectionStatus.CONNECTED:
            logger.warning("XY stage %s is already connected", axis.value)
            return
        
        self.xy_stages[axis].connect(index) # updates stage state

        self._apply_settings()

        self.state.update(
            status=XYStagesStatus.IDLE,
            x_state=self.xy_stages[XY.X_AXIS].state,
            y_state=self.xy_stages[XY.Y_AXIS].state,
            
        )
        logger.info("Connected to xy stage %s", axis.value)


    def disconnect(self, axis: XY) -> None:
        logger.info("Disconnecting from xy stage %s", axis.value)

        self.xy_stages[axis].close() # updates stage state
        self.state.update(
            status=XYStagesStatus.UNKNOWN,
            x_state=self.xy_stages[XY.X_AXIS].state,
            y_state=self.xy_stages[XY.Y_AXIS].state,
        )

    def __acquire_data(self, sleep_time: float | None = None) -> None:
        while self._acquire_data_event.is_set():
            try:
                x_state = self.xy_stages[XY.X_AXIS].get_full_stage_state()
                y_state = self.xy_stages[XY.Y_AXIS].get_full_stage_state()
                timestamp = time.time()

                # print(f"Acquiring data from xy stages: {timestamp}, x: {x_state.position}, y: {y_state.position}")

                data = XYStagesData(
                    timestamp=timestamp,
                    x_position=x_state.position,
                    y_position=y_state.position,
                )

                with Session(engine) as session:
                    session.add(data)
                    session.commit()

                self.ws_manager.broadcast_data_sync(
                    device_name=self.device_name,
                    data=XYStagesDataResponse(
                        device_name=self.device_name,
                        timestamp=[timestamp],
                        x_position=[x_state.position],
                        y_position=[y_state.position],
                    )
                )

                self.state.update(
                    x_state=x_state,
                    y_state=y_state,
                )


            except Exception as e:
                logger.error("Error acquiring data from xy stages: %s", e)
                self.state.update(error=str(e))
                if not self._acquire_data_event.is_set():
                    logger.info("Data acquisition event cleared, stopping thread")
                    break
            finally:
                if sleep_time is not None:
                    time.sleep(sleep_time)
                else:
                    time.sleep(0.2)


    def _start_acquire_data(self, sleep_time: float | None = None) -> None:
        if (
            self._acquire_data_thread is not None
            and self._acquire_data_thread.is_alive()
        ):
            return

        self._acquire_data_event.set()
        self._acquire_data_thread = threading.Thread(
            target=self.__acquire_data, args=(sleep_time,)
        )
        self._acquire_data_thread.start()

        logger.info("Data acquisition thread started for xy stages")

    def _stop_acquire_data(self) -> None:
        if (
            self._acquire_data_thread is None
            or not self._acquire_data_thread.is_alive()
        ):
            logger.warning("Data acquisition thread is not running")
            return

        time.sleep(0.5)  # wait for movement to properly finish before stopping the data acquisition
        self._acquire_data_event.clear()
        self._acquire_data_thread.join()
        self._acquire_data_thread = None
        logger.info("Data acquisition thread stopped for xy stages")

    def _wait_for_movement(self, axis: XY) -> None:
        """
        Wait for the specified axis to finish moving.
        This is a blocking call that will wait until the axis is idle.
        """
        time.sleep(0.5) # wait for the stage to start moving
        while self.xy_stages[axis].state.moving:
            time.sleep(0.2)

    def move_to(self, axis: XY, position: float) -> None:
        """
        Move the specified axis to the given position in mm.
        """
        logger.info("Moving xy stage %s to position %s mm", axis.value, position)

        if self.xy_stages[axis].state.connection_status != ConnectionStatus.CONNECTED:
            raise ValueError(
                f"XY stage {axis.value} is not connected. Please connect first."
            )

        self._start_acquire_data()
        self.state.update(status=XYStagesStatus.MOVING)
        self.xy_stages[axis].move_to(position)
        self._stop_acquire_data()
        self.state.update(status=XYStagesStatus.IDLE)

    def move_by(self, axis: XY, mm: float) -> None:
        """
        Move the specified axis to the given position in mm.
        """
        logger.info("Moving xy stage %s by %s mm", axis.value, mm)

        if self.xy_stages[axis].state.connection_status != ConnectionStatus.CONNECTED:
            raise ValueError(
                f"XY stage {axis.value} is not connected. Please connect first."
            )

        self._start_acquire_data()
        self.state.update(status=XYStagesStatus.MOVING)
        self.xy_stages[axis].move_by(mm)
        self._wait_for_movement(axis)
        self._stop_acquire_data()
        self.state.update(status=XYStagesStatus.IDLE)

    def set_current_position_to_zero(self, axis: XY) -> None:
        """
        Set the current position of the specified axis to zero.
        This is useful for calibrating the stage.
        """
        logger.info("Setting current position of xy stage %s to zero", axis.value)

        if self.xy_stages[axis].state.connection_status != ConnectionStatus.CONNECTED:
            raise ValueError(
                f"XY stage {axis.value} is not connected. Please connect first."
            )

        self._start_acquire_data()
        self.state.update(status=XYStagesStatus.MOVING)
        self.xy_stages[axis].set_zero()
        self._wait_for_movement(axis)
        self._stop_acquire_data()
        self.state.update(status=XYStagesStatus.IDLE)

    def update_settings(self, set_settings: XYStagesSettingsSet):
        logger.info("Updating xy stages wheel settings: %s", set_settings)

        self.settings.update(**set_settings.model_dump(exclude_unset=True))
        current_settings = self.settings.get()

        # apply the settings to the things
        self._apply_settings()

        if self.state.get().error is not None:
            self.settings.undo_last_update()
            raise ValueError(
                f"Error while updating settings for xy stages wheel {self.device_name}: {self.state.get().error}"
            )
        # return the changed settings
        logger.info(
            "Settings updated for xy stages wheel %s: %s",
            self.device_name,
            current_settings.model_dump(exclude_unset=True),
        )
        return self.settings
    
    def _apply_settings(self) -> None:
        current_settings = self.settings.get()
        self.xy_stages[XY.X_AXIS].direction_modifier = current_settings.x_direction_modifier
        self.xy_stages[XY.Y_AXIS].direction_modifier = current_settings.y_direction_modifier

    def shutdown(self) -> None:
        """
        Shutdown the xy stages controller.
        This method should be called when the application is shutting down.
        """
        logger.info("Shutting down xy stages controller")
        self._stop_acquire_data()
        self.disconnect(XY.X_AXIS)
        self.disconnect(XY.Y_AXIS)
