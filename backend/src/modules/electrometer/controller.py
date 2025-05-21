#!/usr/bin/env python3

import asyncio
import csv
import logging
import os
import numpy as np
import pandas as pd
import time
from multiprocessing.connection import Connection
from pathlib import Path
from sqlmodel import Session

import pyvisa
from pyvisa.resources import TCPIPSocket

logger = logging.getLogger()
main_working_directory = Path(__file__).parent.parent

OVERFLOW_UPPER_LIMIT = 1e+35

class KeysightEM:
    def __init__(self, db_session: Session):

        self.rm = pyvisa.ResourceManager("@py")
        self.my_instrument: TCPIPSocket = self._connect_to_keysight_em(self.address)  # type: ignore

        self.db_session = db_session

        self.time_list: list[str] = []
        self.current_list: list[str] = []


    async def init_settings(self):

        await self.write_and_log("*RST")

        await self.write_and_log(
            ":FORM ASC;:FORM:DIG ASC;:FORM:ELEM:CALC CALC,TIME,STAT;:FORM:SREG ASC;"
        )
        await self.write_and_log(":SENS1:FUNC \"CURR\",;")

        await self.set_trigger()

        await self.set_sensor()

        await self.enable_io()
    
    async def _run_blocking(self, func, *args):
        return await asyncio.to_thread(func, *args)

    async def health_check(self) -> bool:
        try:
            error_request = await self._run_blocking(self.my_instrument.query, "SYST:ERR?")
            if error_request != '+0,"No error"':
                logger.error("Error: %s", error_request)
                # clear error
                await self._run_blocking(self.my_instrument.write, "*CLS")
            return True
        except Exception as e:
            logger.error("Error during health check: %s", e)
            return False

    async def start_continuous_measurement(self):
        if self.continuous_measurement_task:
            await self.stop_continuous_measurement()

        logger.info("Starting continuous measurement!")
        await self.write_and_log("*RST")
        await self.set_sensor()
        await self.enable_io()
        self.continuous_measurement_task = asyncio.create_task(self.measure())

    async def stop_continuous_measurement(self):
        logger.info("Stopping continuous measurement!")
        if self.continuous_measurement_task:
            self.continuous_measurement_task.cancel()
            self.settings_handler.read_settings()
        
        self.continuous_measurement_task = None
        await self.turn_off_io()

    async def restart_continuous_measurement_if_running(self):
        if self.continuous_measurement_task:
            logger.info("Restarting continuous measurement task")
            await self.start_continuous_measurement()

    async def measure(self):
        while True:
            await self._run_blocking(self.my_instrument.write, ":INIT:ACQ (@1);")

            await self.wait_for_device_ready()

            cur = await self._run_blocking(self.my_instrument.query, ":FETC:CURR? (@1);")

            try:
                self.time_list = [time.time()]
                self.current_list = [cur]
                self.save_data_to_file()
            except Exception as e:
                logger.error("Error in converting data to float: %s", e)

    async def init_trigger_based_measurement(self):
        logger.info("Initializing trigger based measurement")
        await self.stop_continuous_measurement()
        await self.set_sensor()
        await self.set_trigger()

    async def do_trigger_based_measurement(self):
        await self.enable_io()
        await self.write_and_log(":INIT:ALL (@1);")
        wait_time = int(float(self.COUN) * float(self.TIM))
        logger.info("Waiting for %s seconds to retrieve data", wait_time)
        start = time.time()
        while time.time() - start < wait_time:
            await asyncio.sleep(0.2)
            print(f"Keysight controller info: {(time.time() - start):.2f} / {wait_time:.2f} seconds measurement time", end="\r")
        await self.get_trigger_based_data(start)

    async def set_trigger(self):
        await self.write_and_log(
            f":TRIG1:ALL:SOUR TIM;COUN {self.COUN};TIM {self.TIM};BYP {self.BYP};DEL {self.DEL}"
        )

    async def set_sensor(self):
        #             ":SENS1:CURR:RANG 0.002000;RANG:AUTO OFF;AUTO:ULIM 0.020000;LLIM 0.0001"

        await self.write_and_log(
            f':SENS1:CHAR:APER {self.APER};APER:AUTO {self.APER_AUTO};AUTO:MODE LONG;'
        )
        if self.RANG_AUTO == "ON":
            await self.write_and_log(
                f":SENS1:CURR:RANG:AUTO {self.RANG_AUTO};AUTO:ULIM {self.AUTO_ULIM};LLIM {self.AUTO_LLIM}"
            )
        else:
            await self.write_and_log(
                f":SENS1:CURR:RANG {self.RANG};RANG:AUTO {self.RANG_AUTO}"
            )


    async def enable_io(self):
        await self.write_and_log(":OUTP1 ON;:INP1 ON;")

    async def turn_off_io(self):
        await self.write_and_log(":OUTP1 OFF;:INP1 OFF;")
        # logger.info("Turning off IO -> (disabled for now)")

    def _connect_to_keysight_em(self, ip="192.168.113.72") -> TCPIPSocket:
        try:
            instr: TCPIPSocket = self.rm.open_resource(f"TCPIP::{ip}::5025::SOCKET")  # type: ignore

            # For Serial and TCP/IP socket connections enable the read Termination Character, or read's will timeout
            if instr.resource_name.startswith("ASRL") or instr.resource_name.endswith(
                "SOCKET"
            ):
                instr.read_termination = "\n"

            logger.info("Connected to Keysight EM")

        except pyvisa.errors.VisaIOError as e:
            logger.error("Could not connect to Keysight EM: %s", e)
            raise e

        return instr

    def save_data_to_file(self):
        df = pd.DataFrame({"time": self.time_list, "current": self.current_list})

        if not df.empty:
            # Get the SQLAlchemy engine from the session
            engine = self.db_session.get_bind()

            # Insert directly using pandas to_sql - vectorized operation
            df.to_sql(
                name="em_current_data", con=engine, if_exists="append", index=False
            )

            # Commit the transaction if needed
            self.db_session.commit()

        self.time_list.clear()
        self.current_list.clear()

    async def get_trigger_based_data(self, start_time: float = 0):
        times = self.my_instrument.query(":FETCH:ARR:TIME? (@1);")
        cur = self.my_instrument.query(":FETCH:ARR:CURR? (@1);")
        time_list = times.split(",")
        current_list = cur.split(",")
        try:
            time_arr = np.array(time_list, dtype=float) + start_time
            self.time_list = time_arr.tolist() # type: ignore
            self.current_list = current_list
            self.save_data_to_file()
            await self.turn_off_io()
        except Exception as e:
            logger.error("Error in converting data to float: %s", e)

    async def wait_for_device_ready(self):
        device_ready = False
        while not device_ready:
            resp = await self._run_blocking(self.my_instrument.query, ":STAT:OPER:COND?")
            # print(f"waiting for device to be ready, response: {resp}, bitwise 0b{int(resp):016b}, time {time.time()}")

            await asyncio.sleep(0.05) # wait a bit ...

            # 0b0000010010000010 means not ready -> 1154
            # 0b0000010010010010 means idle -> 1170
    
            if resp == "1170": # 1170 means the device is idle, no pending triggers
                device_ready = True
            else:
                await asyncio.sleep(0.1)

    async def write_and_log(self, command: str):
        try:
            await self.wait_for_device_ready()

            await self._run_blocking(self.my_instrument.write, command)
            logger.info("Write to EM: %s", command)
            error_request = await self._run_blocking(self.my_instrument.query, "SYST:ERR?")
            if error_request != '+0,"No error"':
                logger.error("Error: %s", error_request)
                await self.write_and_log("*CLS")
        except pyvisa.errors.VisaIOError as e:
            logger.error("Write: %s -> Error: %s", command, e)

    def _get_state(self):
        return self.db_session.....