import asyncio
import logging
import numpy as np
import pandas as pd
import time
from sqlmodel import Session

import pyvisa
from pyvisa.resources import TCPIPSocket

from src.core.utils import run_blocking
from src.core.state_manager import DeviceStateManager
from src.modules.electrometer.models import ElectrometerState, ElectrometerID
from src.core.models import ConnectionStatus

logger = logging.getLogger()

class KeysightEM:
    def __init__(self, device_id: ElectrometerID, state_manager: DeviceStateManager[ElectrometerState], db_session: Session):

        self.device_id = device_id

        logger.info("Initializing Keysight EM controller for device ID: %s", device_id)
        self.rm = pyvisa.ResourceManager("@py")
        self.em: TCPIPSocket

        self.state = state_manager
        self.state.get()
        self.state.update(connection_status=ConnectionStatus.DISCONNECTED)

        self.db_session = db_session


        self.time_list: list[str] = []
        self.current_list: list[str] = []


    async def init_settings(self):

        await self._write_and_log("*RST")

        await self._write_and_log(
            ":FORM ASC;:FORM:DIG ASC;:FORM:ELEM:CALC CALC,TIME,STAT;:FORM:SREG ASC;"
        )
        await self._write_and_log(":SENS1:FUNC \"CURR\",;")

        await self.set_trigger()

        await self.set_sensor()

        await self.enable_io()

    async def _health_check(self) -> bool:
        try:
            error_request = await self._em_query("SYST:ERR?")
            if error_request != '+0,"No error"':
                logger.error("Error during health check: %s", error_request)
                # clear error
                await self._em_write("*CLS")
            return True
        except Exception as e:
            logger.error("Error during health check: %s", e)
            return False

    async def start_continuous_measurement(self):
        if self.continuous_measurement_task:
            await self.stop_continuous_measurement()

        logger.info("Starting continuous measurement!")
        await self._write_and_log("*RST")
        await self.set_sensor()
        await self.enable_io()
        self.continuous_measurement_task = asyncio.create_task(self.measure())

    async def stop_continuous_measurement(self):
        logger.info("Stopping continuous measurement!")
        if self.continuous_measurement_task:
            self.continuous_measurement_task.cancel()
        
        self.continuous_measurement_task = None
        await self.turn_off_io()

    async def restart_continuous_measurement_if_running(self):
        if self.continuous_measurement_task:
            logger.info("Restarting continuous measurement task")
            await self.start_continuous_measurement()

    async def measure(self):
        while True:
            await self._em_write(":INIT:ACQ (@1);")

            await self._wait_for_device_ready()

            cur = await self._em_query(":FETC:CURR? (@1);")

            try:
                self.time_list = [time.time()]
                self.current_list = [cur]
                await self._save_data_to_file()
            except Exception as e:
                logger.error("Error in converting data to float: %s", e)

    async def init_trigger_based_measurement(self):
        logger.info("Initializing trigger based measurement")
        await self.stop_continuous_measurement()
        await self.set_sensor()
        await self.set_trigger()

    async def do_trigger_based_measurement(self):
        await self.enable_io()
        await self._write_and_log(":INIT:ALL (@1);")
        wait_time = int(float(self.state.get().trigger_count) * float(self.state.get().trigger_time_interval))
        logger.info("Waiting for %s seconds to retrieve data", wait_time)
        start = time.time()
        while time.time() - start < wait_time:
            await asyncio.sleep(0.2)
            print(f"Keysight controller info: {(time.time() - start):.2f} / {wait_time:.2f} seconds measurement time", end="\r")
        await self._fetch_trigger_based_data(start)

    async def set_trigger(self):
        await self._write_and_log(
            f":TRIG1:ALL:SOUR TIM;COUN {self.state.get().trigger_count};TIM {self.state.get().trigger_time_interval};BYP {self.state.get().trigger_bypass};DEL {self.state.get().trigger_delay}"
        )

    async def set_sensor(self):
        #             ":SENS1:CURR:RANG 0.002000;RANG:AUTO OFF;AUTO:ULIM 0.020000;LLIM 0.0001"

        await self._write_and_log(
            f':SENS1:CHAR:APER {self.state.get().aperture_integration_time};APER:AUTO {self.state.get().aperture_auto};AUTO:MODE LONG;'
        )
        if self.state.get().current_range_auto == "ON":
            await self._write_and_log(
                f":SENS1:CURR:RANG:AUTO {self.state.get().current_range_auto};AUTO:ULIM {self.state.get().current_range_auto_upper_limit};LLIM {self.state.get().current_range_auto_lower_limit};"
            )
        else:
            await self._write_and_log(
                f":SENS1:CURR:RANG {self.state.get().current_range};RANG:AUTO {self.state.get().current_range_auto}"
            )

    async def enable_io(self):
        await self._write_and_log(":OUTP1 ON;:INP1 ON;")

    async def turn_off_io(self):
        await self._write_and_log(":OUTP1 OFF;:INP1 OFF;")


    def connect_to_keysight_em(self, ip="192.168.113.72") -> ElectrometerState:
        try:
            if self.state.get().connection_status != ConnectionStatus.CONNECTED:
                self.em = self.rm.open_resource(f"TCPIP::{ip}::5025::SOCKET")  # type: ignore

                # For Serial and TCP/IP socket connections enable the read Termination Character, or read's will timeout
                if self.em.resource_name.startswith("ASRL") or self.em.resource_name.endswith(
                    "SOCKET"
                ):
                    self.em.read_termination = "\n"

                logger.info("Connected to Keysight EM")

                # testing
                logger.info("Testing connection to EM")
                idn = self.em.query("*IDN?")
                logger.info("IDN: %s", idn)

                # update state to connected
                self.state.update(connection_status=ConnectionStatus.CONNECTED)

            return self.state.get()

        except pyvisa.errors.VisaIOError as e:
            logger.error("Could not connect to Keysight EM: %s", e)
            raise e
        
    async def _save_data_to_file(self):
        def save():
            df = pd.DataFrame({"time": self.time_list, "current": self.current_list})

            if not df.empty:
                # Get the SQLAlchemy engine from the session
                engine = self.db_session.get_bind()

                # Insert directly using pandas to_sql - vectorized operation
                df.to_sql(
                    name="em_current_data", con=engine, if_exists="append", index=False
                )

                # Commit the transaction
                self.db_session.commit()

            self.time_list.clear()
            self.current_list.clear()
        await run_blocking(save)

    async def _fetch_trigger_based_data(self, start_time: float = 0):
        await self._wait_for_device_ready()
        times = await self._em_query(":FETCH:ARR:TIME? (@1);")
        cur = await self._em_query(":FETCH:ARR:CURR? (@1);")
        time_list = times.split(",")
        current_list = cur.split(",")
        try:
            time_arr = np.array(time_list, dtype=float) + start_time
            self.time_list = time_arr.tolist() # type: ignore
            self.current_list = current_list
            await self._save_data_to_file()
            await self.turn_off_io()
        except Exception as e:
            logger.error("Error in converting data to float: %s", e)

    async def _wait_for_device_ready(self):
        device_ready = False
        while not device_ready:
            resp = await self._em_query(":STAT:OPER:COND?")
            # print(f"waiting for device to be ready, response: {resp}, bitwise 0b{int(resp):016b}, time {time.time()}")

            # 0b0000010010000010 means not ready -> 1154
            # 0b0000010010010010 means idle -> 1170
    
            if resp == "1170": # 1170 means the device is idle, no pending triggers
                device_ready = True
            else:
                await asyncio.sleep(0.1)

    async def _write_and_log(self, command: str):
        try:
            await self._wait_for_device_ready()

            logger.info("Write to EM: %s", command)
            await self._em_write(command)

            error_request = await self._em_query("SYST:ERR?")
            if error_request != '+0,"No error"':
                logger.error("Error in _write_and_log: '%s', for query: '%s'", error_request, command)
                await self._write_and_log("*CLS")
        except pyvisa.errors.VisaIOError as e:
            logger.error("Write: %s -> Error: %s", command, e)

    async def _em_query(self, command: str) -> str:
        return await run_blocking(self.em.query, command)

    async def _em_write(self, command: str) -> int:
        return await run_blocking(self.em.write, command)
