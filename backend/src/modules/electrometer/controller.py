import logging
import time
import threading

import pyvisa
import numpy as np
from sqlmodel import Session
from pyvisa.resources import TCPIPSocket

from src.core.config import config
from src.shared.websocket_manager import WebSocketManager
from src.shared.settings_manager import SettingsManager
from src.shared.state_manager import StateManager
from src.modules.electrometer.models import (
    ElectrometerSettings,
    ElectrometerState,
    ElectrometerName,
    ElectrometerData,
    ElectrometerSourceVoltageData,
    ElectrometerDataResponse,
    ElectrometerStatus,
    ElectrometerSettingsSet,
)
from src.shared.models import ConnectionStatus
from src.modules.electrometer.db import engine

logger = logging.getLogger()


class KeysightEM:
    def __init__(
        self,
        device_id: int,
        device_name: ElectrometerName,
        ws_manager: WebSocketManager[
            ElectrometerState, ElectrometerDataResponse, ElectrometerSettings
        ],
    ):
        logger.info(
            "Initializing Keysight EM controller for device ID: %s", device_name.value
        )

        self.device_id = device_id
        self.device_name = device_name
        self.ws_manager = ws_manager
        self.ip_address: str | None = None  # IP address will be set when connecting

        self.rm = pyvisa.ResourceManager("@py")
        self.em: TCPIPSocket

        self.settings: SettingsManager[ElectrometerSettings] = SettingsManager(
            model=ElectrometerSettings,
            device_id=self.device_id,
            device_name=self.device_name.value,
            engine=engine,
            on_settings_update=self.ws_manager.broadcast_setting_sync,
        )

        self.state: StateManager[ElectrometerState] = StateManager(
            model=ElectrometerState,
            device_name=self.device_name.value,
            on_state_update=self.ws_manager.broadcast_state_sync,
        )

        self.continuous_measurement_thread: threading.Thread | None = None
        self._stop_continuous_measurement_event = threading.Event()
        self._pause_continuous_measurement_event = threading.Event()
        self._resume_continuous_measurement_event = threading.Event()

        self.trigger_based_measurement_running = False
        self._voltage_sweep_cancel_event = threading.Event()
        self._previous_voltage_range: float | None = None

        self.time_list: list[str] = []
        self.current_list: list[str] = []

        self._em_lock = threading.Lock()  # thread lock for device access

        # start health check thread
        self.health_check_thread = threading.Thread(target=self._health_check)
        self.health_check_thread.daemon = True
        self.health_check_thread.start()

    def _check_trig_settings(self):
        logger.info(
            "Trigger Byp, TRAN: %s, ACQ: %s",
            self._em_query(":TRIG1:TRAN:BYP?"),
            self._em_query(":TRIG1:ACQ:BYP?"),
        )
        logger.info(
            "Trigger Count, TRAN: %s, ACQ: %s",
            self._em_query(":TRIG1:TRAN:COUN?"),
            self._em_query(":TRIG1:ACQ:COUN?"),
        )
        logger.info(
            "Trigger Source, TRAN: %s, ACQ: %s",
            self._em_query(":TRIG1:TRAN:SOUR?"),
            self._em_query(":TRIG1:ACQ:SOUR?"),
        )
        logger.info(
            "Trigger Delay, TRAN: %s, ACQ: %s",
            self._em_query(":TRIG1:TRAN:DEL?"),
            self._em_query(":TRIG1:ACQ:DEL?"),
        )
        logger.info(
            "Trigger Timer, TRAN: %s, ACQ: %s",
            self._em_query(":TRIG1:TRAN:TIM?"),
            self._em_query(":TRIG1:ACQ:TIM?"),
        )

    def _init_settings(self):
        self.reset_em()
        self._safe_write_and_log(
            ':FORM ASC;:FORM:DIG ASC;:FORM:ELEM:CALC CALC,TIME,STAT;:FORM:SREG ASC;:SENS1:FUNC "CURR",;'
        )
        # set initial source voltage to 'null' to indicate that the state is unknown.
        # since we do not know the state of the output relay and voltage we just set it to null
        self._store_latest_voltage_set(None) 

    def _health_check(self):
        logger.info("Starting health check for Keysight EM %s", self.device_name.value)
        while True:
            # only perform health check if the device is connected and idle
            if (
                self.state.get().connection_status != ConnectionStatus.DISCONNECTED
                and self.state.get().status == ElectrometerStatus.IDLE
            ):
                try:
                    self._wait_for_device_ready()
                    error_request = self._em_query("SYST:ERR?")
                    logger.debug(
                        "Health check response: %s of device %s",
                        error_request,
                        self.device_name.value,
                    )
                    if error_request != '+0,"No error"':
                        logger.error("Error during health check: %s", error_request)
                        self.state.update(
                            error="Error in health check: " + error_request
                        )
                        self._em_write("*CLS")
                except Exception as e:
                    self.state.update(
                        connection_status=ConnectionStatus.HEALTH_CHECK_FAILED,
                        status=ElectrometerStatus.UNKNOWN,
                    )
                    logger.error("Error during health check: %s", e)

            time.sleep(config.HEALTH_CHECK_INTERVAL)

    def start_continuous_measurement(self):
        self.stop_continuous_measurement()
        logger.info("Starting continuous measurement!")
        self._reset_trigger_to_default()  # reset trigger to default settings, needed for continuous measurement to work properly
        self._set_sensor()
        self.enable_input()
        self._stop_continuous_measurement_event.clear()
        self.continuous_measurement_thread = threading.Thread(target=self.__measure)
        self.continuous_measurement_thread.start()

    def stop_continuous_measurement(self):
        if (
            self.continuous_measurement_thread
            and self.continuous_measurement_thread.is_alive()
        ):
            logger.info("Stopping continuous measurement!")
            self._stop_continuous_measurement_event.set()  # signal the thread to stop
            self.continuous_measurement_thread.join()
        self.continuous_measurement_thread = None
        self.disable_input()
        # state is set in measurement thread when it stops

    def __measure(self):
        self.state.update(
            status=ElectrometerStatus.WAITING_TO_START_CONTINUOUS_MEASUREMENT
        )
        first_datapoint_received = False
        while not self._stop_continuous_measurement_event.is_set():
            if self._pause_continuous_measurement_event.is_set():
                logger.info(
                    "Continuous measurement paused for %s", self.device_name.value
                )
                self._resume_continuous_measurement_event.wait()

            self._em_write(":INIT:ACQ (@1);")
            self._wait_for_device_ready()
            cur = self._em_query(":FETC:CURR? (@1);")
            try:
                # make sure the cur is a float
                cur = float(cur)
                self.time_list = [time.time()]
                self.current_list = [cur]
                if not first_datapoint_received and cur:
                    first_datapoint_received = True
                    self.state.update(
                        status=ElectrometerStatus.CONTINUOUS_MEASUREMENT_RUNNING
                    )

                logger.debug(f"{self.device_name.value} - Fetched current: %s", cur)
                self._save_data()
            except Exception as e:
                logger.error("Error in converting data to float: %s", e)
            time.sleep(0.01)  # Add a sleep to avoid tight loop
        self.state.update(status=ElectrometerStatus.IDLE)

    def _init_trigger_based_measurement(self):
        logger.info("Initializing trigger based measurement")
        self.stop_continuous_measurement()
        self._set_sensor()
        self._set_trigger()

    def do_trigger_based_measurement(self):
        if self.trigger_based_measurement_running:
            logger.warning("Trigger based measurement is already running!")
        else:
            try:
                self._init_trigger_based_measurement()
                self.trigger_based_measurement_running = True
                self.state.update(
                    status=ElectrometerStatus.TRIGGER_BASED_MEASUREMENT_RUNNING
                )
                logger.info("Starting trigger based measurement")
                if self.state.get().output_status != "ON":
                    self.enable_output()  # output relay needs to be enabled for INIT:ALL
                self.enable_input()
                self._safe_write_and_log(":INIT:ALL (@1);")
                wait_time = int(
                    float(self.settings.get().trigger_count)
                    * float(self.settings.get().trigger_time_interval)
                )
                logger.info("Waiting for %s seconds to retrieve data", wait_time)
                start = time.time()
                while time.time() - start < wait_time:
                    time.sleep(0.2)
                    progress = f"{(time.time() - start):.2f} / {wait_time:.2f}"
                    print(
                        f"Keysight controller info: {progress} seconds measurement time",
                        end="\r",
                    )
                    self.state.update(
                        status=ElectrometerStatus.TRIGGER_BASED_MEASUREMENT_RUNNING,
                        trigger_based_measurement_status=f"{progress} seconds",
                    )
                self.state.update(
                    status=ElectrometerStatus.FETCHING_TRIGGER_BASED_MEASUREMENT_DATA,
                    trigger_based_measurement_status="Fetching data ...",
                )
                self._fetch_trigger_based_data(start)

            except Exception as e:

                logger.error("Error during trigger based measurement: %s", e)
                self.state.update(
                    error=str(e)
                )

            finally:
                self.disable_input()
                self.trigger_based_measurement_running = False
                self.state.update(
                    status=ElectrometerStatus.IDLE, trigger_based_measurement_status="Done"
                )

    def update_settings(self, set_settings: ElectrometerSettingsSet):
        logger.info("Updating settings for Keysight EM %s", self.device_name.value)

        self.settings.update(**set_settings.model_dump(exclude_unset=True))
        current_settings = self.settings.get()

        self._set_sensor()
        self._set_trigger()

        if self.state.get().error is not None:
            self.settings.undo_last_update()
            raise ValueError(
                f"Error while updating settings for Keysight EM {self.device_name.value}: {self.state.get().error}"
            )
        # return the changed settings
        logger.info(
            "Settings updated for Keysight EM %s: %s",
            self.device_name.value,
            current_settings.model_dump(exclude_unset=True),
        )
        return self.settings

    def _set_trigger(self):
        self._safe_write_and_log(
            f":TRIG1:ALL:SOUR TIM;COUN {self.settings.get().trigger_count};TIM {self.settings.get().trigger_time_interval};BYP {self.settings.get().trigger_bypass};DEL {self.settings.get().trigger_delay}"
        )

    def _reset_trigger_to_default(self):
        self._safe_write_and_log(":TRIG1:ALL:SOUR AINT;COUN 1;TIM 1e-4;BYP OFF;DEL 0")

    def _set_sensor(self):
        aperture_command = f":SENS1:CHAR:APER {self.settings.get().aperture_integration_time};APER:AUTO {self.settings.get().aperture_auto};AUTO:MODE LONG;"
        if self.settings.get().current_range_auto == "ON":
            self._safe_write_and_log(
                f"{aperture_command}:SENS1:CURR:RANG:AUTO {self.settings.get().current_range_auto};AUTO:ULIM {self.settings.get().current_range_auto_upper_limit};LLIM {self.settings.get().current_range_auto_lower_limit};"
            )
        else:
            self._safe_write_and_log(
                f"{aperture_command}:SENS1:CURR:RANG {self.settings.get().current_range};RANG:AUTO {self.settings.get().current_range_auto}"
            )

    def _generate_sweep_voltages_with_zero(
        self, start: float, stop: float, step: float
    ) -> list[float]:
        if step == 0:
            raise ValueError("Step must not be zero")

        if (stop - start) * step <= 0:
            raise ValueError("Step direction does not lead toward stop")

        voltages = [start]

        # Generate voltages list
        while (step > 0 and voltages[-1] + step < stop) or (
            step < 0 and voltages[-1] + step > stop
        ):
            voltages.append(voltages[-1] + step)

        if voltages[-1] != stop:
            voltages.append(stop)

        # Check if zero is already in the list
        if 0 in voltages:
            return voltages

        # Check if we cross zero (in either direction)
        for i in range(len(voltages) - 1):
            v1, v2 = voltages[i], voltages[i + 1]
            if (v1 < 0 and v2 > 0) or (v1 > 0 and v2 < 0):
                voltages.insert(i + 1, 0.0)
                break

        return voltages

    def _set_source_voltage_with_range(
        self, voltage: float, prev_range: float | None = None
    ) -> float:
        # decide range based on voltage sign
        v_range = 1000 if voltage >= 0 else -1000

        # only change range if it is different from previous one
        if prev_range is None:
            logger.info("Setting initial voltage range to %s V", v_range)
            self._safe_write_and_log(f":SOUR1:VOLT:RANG {v_range};")
        elif v_range != prev_range:
            logger.info(
                "Switching voltage range to %s V, disabling output temporarily.",
                v_range,
            )
            self._pause_continuous_measurement()
            self.disable_output()
            self._safe_write_and_log(f":SOUR1:VOLT:RANG {v_range};")
            self.enable_output()
            self._resume_continuous_measurement()

        logger.info("Setting source voltage to %s V", voltage)
        self._safe_write_and_log(f":SOUR1:VOLT {voltage};")
        set_value = self._em_query("SOUR1:VOLT?")
        self.state.update(source_voltage_status=f"{float(set_value)} V")
        self._store_latest_voltage_set(float(set_value))
        return v_range

    def _store_latest_voltage_set(self, voltage: float | None):
        data = ElectrometerSourceVoltageData(
            device_id=self.device_id,
            timestamp=time.time(),
            source_voltage=voltage,
        )
        with Session(engine) as session:
            session.add(data)
            session.commit()

    def _pause_continuous_measurement(self):
        """Pause the continuous measurement for the Keysight EM."""
        logger.info("Pausing continuous measurement for %s", self.device_name.value)
        time.sleep(0.3)  # give some time to pause the measurement
        self._pause_continuous_measurement_event.set()

    def _resume_continuous_measurement(self):
        """Resume the continuous measurement for the Keysight EM."""
        logger.info("Resuming continuous measurement for %s", self.device_name.value)
        self._resume_continuous_measurement_event.set()
        time.sleep(0.3)
        self._pause_continuous_measurement_event.clear()
        self._resume_continuous_measurement_event.clear()

    def do_source_voltage_sweep(self):
        """Do the source voltage sweep for the Keysight EM."""
        logger.info(
            "Do source voltage sweep with %s",
            self.device_name.value,
        )

        self.state.update(source_voltage_status="Starting source voltage sweep ...")

        # this is terribly ugly and should be cleaned up, basically we need to pause the continuous measurement for the trigger to become idle, then we can set the source voltage stuff
        # maybe we can fix this with context managers or something similar in the future, for now it works ...
        self._pause_continuous_measurement()
        # command as sent by old labview code: :SOUR1:FUNC:MODE VOLT;:SOUR1:FUNC:TRIG:CONT OFF;:SOUR1:VOLT:TRIG 0.000000;:SOUR1:VOLT 0.000000;:SOUR1:VOLT:RANG 1000.000000;:SOUR1:VOLT:RLIM:STAT OFF;
        self.disable_output()
        self._safe_write_and_log(
            ":OUTP1:OFF:MODE ZERO;:OUTP1:LOW COMM;:SOUR1:FUNC:MODE VOLT;:SOUR1:FUNC:TRIG:CONT OFF;:SOUR1:VOLT 0;:SOUR1:VOLT:TRIG 0;:SOUR1:VOLT:RLIM:STAT OFF;"
        )
        self._voltage_sweep_cancel_event.clear()  # reset the cancel event
        self._previous_voltage_range = self._set_source_voltage_with_range(
            0, None
        )  # set initial voltage to 0 and range to 1000 V

        self._resume_continuous_measurement()

        voltages = self._generate_sweep_voltages_with_zero(
            self.settings.get().voltage_start,
            self.settings.get().voltage_stop,
            self.settings.get().voltage_step,
        )

        self.enable_output()
        for v in voltages:
            if self._voltage_sweep_cancel_event.is_set():
                logger.info("Voltage sweep cancelled.")
                self._voltage_sweep_cancel_event.clear()
                break
            self._previous_voltage_range = self._set_source_voltage_with_range(v, self._previous_voltage_range)
            time.sleep(self.settings.get().voltage_settle_time)

    def turn_off_source_voltage(self):
        """Turn off the source voltage for the Keysight EM."""
        logger.info("Turning off source voltage for %s", self.device_name.value)
        if self.state.get().output_status != "ON":
            logger.info("Source voltage output is already off.")
            return
        
        self._voltage_sweep_cancel_event.set()  # cancel any ongoing voltage sweep
        latest_voltage:float = float(self._em_query("SOUR1:VOLT?"))
        voltages = self._generate_sweep_voltages_with_zero(
            latest_voltage, 0, np.sign(latest_voltage) * -1 * self.settings.get().voltage_step
        )

        for v in voltages:
            self._previous_voltage_range = self._set_source_voltage_with_range(v, self._previous_voltage_range)
            time.sleep(self.settings.get().voltage_settle_time)
            
        self._set_source_voltage_with_range(0, 1000)
        self.disable_output()

    def enable_input(self):
        self._safe_write_and_log(":INP1 ON;")
        self.state.update(input_status="ON")

    def enable_output(self):
        self._safe_write_and_log(":OUTP1 ON;")
        self.state.update(output_status="ON")

    def disable_input(self):
        self._safe_write_and_log(":INP1 OFF;")
        self.state.update(input_status="OFF")

    def disable_output(self):
        self._safe_write_and_log(":OUTP1 OFF;")
        self.state.update(output_status="OFF")

    def reset_em(self):
        self._em_write("*RST")

    def connect_to_keysight_em(self, ip) -> str:
        try:
            if self.state.get().connection_status != ConnectionStatus.CONNECTED:
                self.state.update(connection_status=ConnectionStatus.CONNECTING)
                self.em = self.rm.open_resource(f"TCPIP::{ip}::5025::SOCKET")  # type: ignore

                # For Serial and TCP/IP socket connections enable the read Termination Character, or read's will timeout
                if self.em.resource_name.startswith(
                    "ASRL"
                ) or self.em.resource_name.endswith("SOCKET"):
                    self.em.read_termination = "\n"

                logger.info("Connected to Keysight EM")

                # update state to connected
                self.state.update(
                    connection_status=ConnectionStatus.CONNECTED,
                    status=ElectrometerStatus.IDLE,
                )

                self.ip_address = ip
            # testing connection
            logger.info("Testing connection to EM %s at %s", self.device_name.value, ip)
            idn = self._em_query("*IDN?")
            logger.info("*IDN?: %s", idn)
            return idn
        except Exception as e:
            self.state.update(
                connection_status=ConnectionStatus.DISCONNECTED,
                status=ElectrometerStatus.UNKNOWN,
                error=f"Could not connect to Keysight EM at {ip}: {e}",
            )
            logger.error("Could not connect to Keysight EM: %s", e)
            raise e

    def disconnect_from_keysight_em(self):
        try:
            logger.info(
                "Disconnecting from Keysight EM %s at %s",
                self.device_name.value,
                self.ip_address,
            )
            self.ip_address = None  # clear the IP address
            self.stop_continuous_measurement()
            self.em.close()
            self.state.update(
                connection_status=ConnectionStatus.DISCONNECTED,
                status=ElectrometerStatus.UNKNOWN,
            )
            logger.info("Disconnected from Keysight EM %s", self.device_name.value)
        except Exception as e:
            logger.error("Error while disconnecting: %s", e)


    def _save_data(self):
        data: list[ElectrometerData] = []

        for timestamp, current in zip(self.time_list, self.current_list):
            cur = float(current)
            if abs(cur) > 1e30:  # if the current is too high, skip this measurement
                self.state.update(
                    error=f"Current value {cur} is too high, overflow! -> Adjust current limits."
                )
                raise ValueError(f"Current value {cur} is too high, overflow!")

            data.append(
                ElectrometerData(
                    device_id=self.device_id,
                    timestamp=float(timestamp),
                    current=cur,
                )
            )

        # save to db
        if len(data) > 0:
            with Session(engine) as session:
                session.add_all(data)
                session.commit()

            current_data_response = ElectrometerDataResponse(
                device_name=self.device_name.value,
                current=self.current_list,
                timestamp=self.time_list,
            )
            self.ws_manager.broadcast_data_sync(
                self.device_name.value, current_data_response
            )

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

    def _safe_write_and_log(self, command: str):
        try:
            self._wait_for_device_ready()
            logger.info("Write to EM: %s", command)
            self._em_write(command)
            error_request = self._em_query("SYST:ERR?")
            if error_request != '+0,"No error"':
                error_string = (
                    f"Error in _write_and_log: {error_request}, command: {command}"
                )
                logger.error(error_string)
                self.state.update(error=error_string)
                self._safe_write_and_log("*CLS")
        except pyvisa.errors.VisaIOError as e:
            logger.error("Write: %s -> Error: %s", command, e)

    def _em_query(self, command: str) -> str:
        with self._em_lock:
            return self.em.query(command)

    def _em_write(self, command: str) -> int:
        with self._em_lock:
            return self.em.write(command)

    def shutdown(self):
        """
        Shutdown the controller, disconnect from the device and clean up resources.
        """
        logger.info("Shutting down Keysight EM %s", self.device_name.value)
        self.health_check_thread.join(timeout=1)
        if self.state.get().connection_status == ConnectionStatus.CONNECTED:
            self.stop_continuous_measurement()
            self.disconnect_from_keysight_em()
