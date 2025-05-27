import logging
import time
import threading

import pyvisa
import numpy as np
from sqlmodel import Session
from pyvisa.resources import TCPIPSocket

from src.shared.websocket_manager import WebSocketManager
from src.shared.state_manager import DeviceStateManager
from src.modules.electrometer.models import ElectrometerState, ElectrometerID, CurrentData, CurrentDataResponse, ElectrometerStatus
from src.shared.models import ConnectionStatus

logger = logging.getLogger()


class KeysightEM:
    def __init__(
        self,
        device_id: ElectrometerID,
        db_session: Session,
        ws_manager: WebSocketManager[ElectrometerState, CurrentDataResponse],
    ):
        logger.info("Initializing Keysight EM controller for device ID: %s", device_id)

        self.device_id = device_id
        self.db_session = db_session
        self.ws_manager = ws_manager

        self.rm = pyvisa.ResourceManager("@py")
        self.em: TCPIPSocket

        self.state: DeviceStateManager[ElectrometerState] = DeviceStateManager(
            model=ElectrometerState,
            device_id=self.device_id,
            session=self.db_session,
            on_state_update=self.ws_manager.broadcast_state_sync
        )
        self.state.update(connection_status=ConnectionStatus.DISCONNECTED, status=ElectrometerStatus.unknown)

        self.continuous_measurement_thread: threading.Thread | None = None
        self._stop_continuous_measurement_event = threading.Event()

        self.trigger_based_measurement_running = False

        self.time_list: list[str] = []
        self.current_list: list[str] = []

    def init_settings(self):
        self._write_and_log("*RST")
        self._write_and_log(
            ':SENS1:FUNC "CURR",;:FORM ASC;:FORM:DIG ASC;:FORM:ELEM:CALC CALC,TIME,STAT;:FORM:SREG ASC;'
        )
        self.set_trigger()
        self.set_sensor()
        self.enable_io()

    def health_check(self) -> bool:
        try:
            error_request = self._em_query("SYST:ERR?")
            if error_request != '+0,"No error"':
                logger.error("Error during health check: %s", error_request)
                self.state.update(connection_status=ConnectionStatus.HEALTH_CHECK_FAILED, status=ElectrometerStatus.unknown)
                self._em_write("*CLS")
            return True
        except Exception as e:
            logger.error("Error during health check: %s", e)
            return False

    def start_continuous_measurement(self):
        self.stop_continuous_measurement()
        logger.info("Starting continuous measurement!")
        self._write_and_log("*RST")
        self.set_sensor()
        self.enable_io()
        self._stop_continuous_measurement_event.clear()
        self.continuous_measurement_thread = threading.Thread(target=self.measure)
        self.continuous_measurement_thread.start()

    def stop_continuous_measurement(self):
        logger.info("Stopping continuous measurement!")
        if (
            self.continuous_measurement_thread
            and self.continuous_measurement_thread.is_alive()
        ):
            self._stop_continuous_measurement_event.set()
            self.continuous_measurement_thread.join()
        self.continuous_measurement_thread = None
        self.turn_off_io()

    def restart_continuous_measurement_if_running(self):
        if (
            self.continuous_measurement_thread
            and self.continuous_measurement_thread.is_alive()
        ):
            logger.info("Restarting continuous measurement thread")
            self.start_continuous_measurement()

    def measure(self):
        while not self._stop_continuous_measurement_event.is_set():
            self._em_write(":INIT:ACQ (@1);")
            self._wait_for_device_ready()
            cur = self._em_query(":FETC:CURR? (@1);")
            try:
                # make sure the cur is a float
                cur = float(cur)
                self.time_list = [time.time()]
                self.current_list = [cur]
                logger.info(f"{self.device_id} - Fetched current: %s", cur)
                self._save_data()
            except Exception as e:
                logger.error("Error in converting data to float: %s", e)
            time.sleep(0.01)  # Add a sleep to avoid tight loop

    def init_trigger_based_measurement(self):
        logger.info("Initializing trigger based measurement")
        self.stop_continuous_measurement()
        self.set_sensor()
        self.set_trigger()

    def do_trigger_based_measurement(self):
        if self.trigger_based_measurement_running:
            logger.warning(
                "Trigger based measurement is already running!"
            )
            
        else:
            self.trigger_based_measurement_running = True
            self.state.update(status=ElectrometerStatus.performing_measurement)
            logger.info("Starting trigger based measurement")
            self.enable_io()
            self._write_and_log(":INIT:ALL (@1);")
            wait_time = int(
                float(self.state.get().trigger_count)
                * float(self.state.get().trigger_time_interval)
            )
            logger.info("Waiting for %s seconds to retrieve data", wait_time)
            start = time.time()
            while time.time() - start < wait_time:
                time.sleep(0.2)
                print(
                    f"Keysight controller info: {(time.time() - start):.2f} / {wait_time:.2f} seconds measurement time",
                    end="\r",
                )
            self._fetch_trigger_based_data(start)
            self.trigger_based_measurement_running = False
            self.state.update(status=ElectrometerStatus.idle)

    def set_trigger(self):
        self._write_and_log(
            f":TRIG1:ALL:SOUR TIM;COUN {self.state.get().trigger_count};TIM {self.state.get().trigger_time_interval};BYP {self.state.get().trigger_bypass};DEL {self.state.get().trigger_delay}"
        )

    def set_sensor(self):
        aperture_command = f":SENS1:CHAR:APER {self.state.get().aperture_integration_time};APER:AUTO {self.state.get().aperture_auto};AUTO:MODE LONG;"
        if self.state.get().current_range_auto == "ON":
            self._write_and_log(
                f"{aperture_command}:SENS1:CURR:RANG:AUTO {self.state.get().current_range_auto};AUTO:ULIM {self.state.get().current_range_auto_upper_limit};LLIM {self.state.get().current_range_auto_lower_limit};"
            )
        else:
            self._write_and_log(
                f"{aperture_command}:SENS1:CURR:RANG {self.state.get().current_range};RANG:AUTO {self.state.get().current_range_auto}"
            )

    def enable_io(self):
        self._write_and_log(":OUTP1 ON;:INP1 ON;")

    def turn_off_io(self):
        self._write_and_log(":OUTP1 OFF;:INP1 OFF;")

    def connect_to_keysight_em(self, ip) -> str:
        try:
            if self.state.get().connection_status != ConnectionStatus.CONNECTED:
                self.em = self.rm.open_resource(f"TCPIP::{ip}::5025::SOCKET")  # type: ignore

                # For Serial and TCP/IP socket connections enable the read Termination Character, or read's will timeout
                if self.em.resource_name.startswith(
                    "ASRL"
                ) or self.em.resource_name.endswith("SOCKET"):
                    self.em.read_termination = "\n"

                logger.info("Connected to Keysight EM")

                # update state to connected
                self.state.update(connection_status=ConnectionStatus.CONNECTED, status=ElectrometerStatus.idle)

            # testing connection
            logger.info("Testing connection to EM %s at %s", self.device_id, ip)
            idn = self.em.query("*IDN?")
            logger.info("*IDN?: %s", idn)
            return idn
        except pyvisa.errors.VisaIOError as e:
            logger.error("Could not connect to Keysight EM: %s", e)
            raise e
    
    def disconnect_from_keysight_em(self):
        if self.state.get().connection_status == ConnectionStatus.CONNECTED:
            try:
                logger.info("Disconnecting from Keysight EM %s", self.device_id)
                self.em.close()
                self.state.update(connection_status=ConnectionStatus.DISCONNECTED, status=ElectrometerStatus.unknown)
                logger.info("Disconnected from Keysight EM %s", self.device_id)
            except pyvisa.errors.VisaIOError as e:
                logger.error("Error while disconnecting: %s", e)
        else:
            logger.warning("EM %s is not connected, cannot disconnect.", self.device_id)

    def _save_data(self):
        data: list[CurrentData] = []

        for timestamp, current in zip(self.time_list, self.current_list):
            data.append(
                CurrentData(
                    device_id=self.device_id,
                    time=float(timestamp),
                    current=float(current),
                )
            )

        # save to db
        if len(data) > 0:
            self.db_session.add_all(data)
            self.db_session.commit()
            current_data_response = CurrentDataResponse(
                device_id=self.device_id,
                current=self.current_list,
                time=self.time_list,
            )
            self.ws_manager.broadcast_data_sync(self.device_id.value, current_data_response)

        self.time_list.clear()
        self.current_list.clear()


    def _fetch_trigger_based_data(self, start_time: float = 0):
        self._wait_for_device_ready()
        times = self._em_query(":FETCH:ARR:TIME? (@1);")
        cur = self._em_query(":FETCH:ARR:CURR? (@1);")
        time_list = times.split(",")
        current_list = cur.split(",")
        try:
            time_arr = np.array(time_list, dtype=float) + start_time
            self.time_list = time_arr.tolist()  # type: ignore
            self.current_list = current_list
            self._save_data()
            self.turn_off_io()
        except Exception as e:
            logger.error("Error in converting data to float: %s", e)

    def _wait_for_device_ready(self):
        device_ready = False
        while not device_ready:
            resp = self._em_query(":STAT:OPER:COND?")
            # print(f"waiting for device to be ready, response: {resp}, bitwise 0b{int(resp):016b}, time {time.time()}")

            # 0b0000010010000010 means not ready -> 1154
            # 0b0000010010010010 means idle -> 1170

            if resp == "1170":  # 1170 means the device is idle, no pending triggers
                device_ready = True
            else:
                time.sleep(0.1)

    def _write_and_log(self, command: str):
        try:
            self._wait_for_device_ready()
            logger.info("Write to EM: %s", command)
            self._em_write(command)
            error_request = self._em_query("SYST:ERR?")
            if error_request != '+0,"No error"':
                logger.error(
                    "Error in _write_and_log: '%s', for query: '%s'",
                    error_request,
                    command,
                )
                self._write_and_log("*CLS")
        except pyvisa.errors.VisaIOError as e:
            logger.error("Write: %s -> Error: %s", command, e)

    def _em_query(self, command: str) -> str:
        return self.em.query(command)

    def _em_write(self, command: str) -> int:
        return self.em.write(command)
