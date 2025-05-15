#!/usr/bin/env python3

import asyncio
import csv
import logging
import os
import numpy as np
import time
from multiprocessing.connection import Connection
from pathlib import Path

import pyvisa
from pyvisa.resources import TCPIPSocket
from util.controller_base import ControllerBase
from util.settings_handler import SettingsHandler

logger = logging.getLogger()
main_working_directory = Path(__file__).parent.parent

OVERFLOW_UPPER_LIMIT = 1e+35

class KeysightEM(ControllerBase):
    def __init__(self, address, pipe: Connection, settings_handler: SettingsHandler):
        super().__init__(address, pipe, settings_handler)

        self.rm = pyvisa.ResourceManager("@py")
        self.my_instrument: TCPIPSocket = self.connect_to_keysight_em(self.address)  # type: ignore

        self.time_list: list[str] = []
        self.current_list: list[str] = []

        self.continuous_measurement_task = None
        self.continuous_measurement_interval = 0.1

        s = self.settings_handler.read_settings()
        self.COUN = s["trigger_count"]
        self.TIM = s["trigger_time_interval"]
        self.BYP = "OFF"
        self.DEL = "0.000000"

        self.FUNC = "CURR"
        self.APER = s["aperture_integration_time"]
        self.APER_AUTO = "OFF"
        self.RANG = s["current_range"]
        self.RANG_AUTO = s["current_range_auto"]
        self.AUTO_ULIM = s["current_range_auto_upper_limit"]
        self.AUTO_LLIM = s["current_range_auto_lower_limit"]

        logger.info("Keysight EM Controller initialized")

        self.init_settings()

        self.listening_starter()

    def listening_starter(self):
        try:
            asyncio.run(self.start_listening())

        except Exception as e:
            logger.warning(
                "Exception occurred in start_listening() method. emptying pipe..."
            )
            logger.error(e)
            time.sleep(0.5)
            self.clear_pipe()
            time.sleep(0.5)
            logger.warning(
                "restart the listening loop and reinitialize the settings..."
            )
            self.init_settings()
            time.sleep(2)
            self.pipe.send("restart")
            self.listening_starter()

    async def start_listening(self):
        logger.info("Keysight EM Controller is listening for commands.")

        loop = asyncio.get_event_loop()
        loop.create_task(self.send_status_data())

        while True:
            # pipe.revc is blocking, so we need to run it in a separate thread to not block the event loop
            # threads produce a lot of overhead, so this is only fine as long as we dont recieve a lot of commands within seconds
            received_command: str = await loop.run_in_executor(None, self.pipe.recv)
            command: str = received_command.split(" ")[0]

            match command:
                case "do_trigger_based_measurement":
                    self.do_trigger_based_measurement()
                case "start_continuous_measurement":
                    await self.start_continuous_measurement()
                case "stop_continuous_measurement":
                    await self.stop_continuous_measurement()
                case "get_data":
                    self.get_trigger_based_data()
                case "get_settings":
                    self.print_settings()
                case "settings_changed":
                    self.settings_changed()
                case "exit":
                    logger.info("exiting...")
                    break
                case _:
                    logger.info("Unknown command")

    def settings_changed(self):
        self.settings_handler.read_settings()
        changed_settings = self.settings_handler.get_changed_settings()
        for setting, value in changed_settings.items():
            match setting:
                case "continuous_measurement_interval":
                    logger.info(
                        "attempting to set continuous_measurement_interval to %s",
                        value,
                    )
                    self.continuous_measurement_interval = value
                case "trigger_time_interval":
                    logger.info(
                        "attempting to set trigger_time_interval set to %s",
                        value,
                    )
                    self.TIM = value
                    self.set_trigger()
                case "trigger_count":
                    logger.info("attempting to set trigger_count set to %s", value)
                    self.COUN = value
                    self.set_trigger()
                case "aperture_integration_time":
                    logger.info(
                        "attempting to set aperture_integration_time set to %s",
                        value,
                    )
                    self.APER = value
                    self.set_sensor()
                case "current_range":
                    logger.info("attempting to set current_range set to %s", value)
                    self.RANG = value
                    self.set_sensor()
                case "current_range_auto":
                    logger.info("attempting to set current_range_auto set to %s", value)
                    self.RANG_AUTO = value
                    self.set_sensor()
                case "current_range_auto_upper_limit":
                    logger.info(
                        "attempting to set ccontinuous_measurement_intervalurrent_range_auto_upper_limit set to %s",
                        value,
                    )
                    self.AUTO_ULIM = value
                    self.set_sensor()
                case "current_range_auto_lower_limit":
                    logger.info(
                        "attempting to set current_range_auto_lower_limit set to %s",
                        value,
                    )
                    self.AUTO_LLIM = value
                    self.set_sensor()
                case "filename":
                    self.filename = value
                    logger.info("filename set to %s", value)

    def init_settings(self):
        self.write_and_log("*CLS")
        self.write_and_log("*RST")

        self.write_and_log(
            ":FORM ASC;:FORM:DIG ASC;:FORM:ELEM:CALC CALC,TIME,STAT;:FORM:SREG ASC;"
        )
        self.write_and_log(":SENS1:FUNC \"CURR\",;")

        # TODO: Check if this is needed
        #                           :OUTP1:LOW COMM;:OUTP1:OFF:MODE ZERO;
        self.write_and_log(":OUTP1:LOW COMM;:OUTP1:OFF:MODE ZERO;")

        #                           :SOUR1:FUNC:MODE VOLT;:SOUR1:FUNC:TRIG:CONT OFF;:SOUR1:VOLT:TRIG 0.000
        self.write_and_log(":SOUR1:FUNC:MODE VOLT;:SOUR1:FUNC:TRIG:CONT OFF;:SOUR1:VOLT:TRIG 0.000")


        self.set_trigger()

        self.set_sensor()


    def print_settings(self):
        print(
            {
                "trigger_count": self.COUN,
                "trigger_time_interval": self.TIM,
                "aperture_integration_time": self.APER,
                "current_range": self.RANG,
                "current_range_auto": self.RANG_AUTO,
                "current_range_auto_upper_limit": self.AUTO_ULIM,
                "current_range_auto_lower_limit": self.AUTO_LLIM,
                "continuous_measurement_interval": self.continuous_measurement_interval,
                "filename": self.filename,
            }
        )

    async def send_status_data(self):
        while True:
            self.pipe.send(
                {
                    "status_data": {},
                    "healthy": await self.health_check(),
                }
            )
            await asyncio.sleep(self.send_status_data_timeout)

    async def health_check(self) -> bool:
        try:
            # test = self.my_instrument.query("*IDN?")
            # print(f"Connected to: {test}")
            # error_request = self.my_instrument.query("SYST:ERR?")
            # if error_request != '+0,"No error"':
            #     logger.error("Error: %s", error_request)
            #     # clear error
            #     self.write_and_log("*CLS")
            return True
        except Exception as e:
            logger.error("Error during health check: %s", e)
            return False

    async def start_continuous_measurement(self):
        # await self.stop_continuous_measurement()

        self.set_sensor()


        self.enable_io()
        self.continuous_measurement_task = asyncio.create_task(self.measure())

    async def stop_continuous_measurement(self):
        self.turn_off_io()
        if self.continuous_measurement_task:
            self.continuous_measurement_task.cancel()

            self.settings_handler.read_settings()
            self.TIM = self.settings_handler.settings["trigger_time_interval"]
            self.COUN = self.settings_handler.settings["trigger_count"]
            self.set_trigger()

    async def measure(self):
        self.write_and_log("*CLS")
        self.write_and_log("*RST")
        self.write_and_log(":FORM ASC;:FORM:DIG ASC;:FORM:ELEM:CALC CALC,TIME,STAT;:FORM:SREG ASC;")
        self.write_and_log(':SENS1:FUNC "CURR",;')
        self.write_and_log(":OUTP1:LOW COMM;:OUTP1:OFF:MODE ZERO;")
        self.write_and_log(":SOUR1:FUNC:MODE VOLT;:SOUR1:FUNC:TRIG:CONT OFF;:SOUR1:VOLT:TRIG 0.000")
        self.write_and_log(":SENS1:CHAR:APER 0.2;APER:AUTO OFF;AUTO:MODE LONG;")
        self.write_and_log(":SENS1:CURR:RANG 2.000000E-6;RANG:AUTO ON;AUTO:ULIM 100e-9;LLIM 1e-16")
        self.write_and_log(":OUTP1 ON;")
        self.write_and_log(":INP1 ON;")
        while True:
            self.my_instrument.write(":INIT:ACQ (@1);")
            print("init aquire over")


            device_ready = False
            while not device_ready:
                resp = self.my_instrument.query(":STAT:OPER:COND?")

                print(f"waiting for device to be ready, current status: {resp}")

                if resp == "1170":
                    device_ready = True
                    await asyncio.sleep(0.1)

            cur = self.my_instrument.query(":FETC:CURR? (@1);")
            print(f"current value: {cur}")

            try:
                self.time_list = [time.time()]
                self.current_list = [cur]
                self.save_data_to_file()
            except Exception as e:
                logger.error("Error in converting data to float: %s", e)

    def do_trigger_based_measurement(self):
        self.enable_io()
        self.write_and_log(":INIT:ALL (@1);")
        wait_time = int(float(self.COUN) * float(self.TIM))
        logger.info("Waiting for %s seconds to retrieve data", wait_time)
        start = time.time()
        while time.time() - start < wait_time:
            time.sleep(0.2)
            print(f"Keysight controller info: {(time.time() - start):.2f} / {wait_time:.2f} seconds measurement time", end="\r")
        self.get_trigger_based_data(start)

    def set_trigger(self):
        self.write_and_log(
            f":TRIG1:ALL:SOUR TIM;COUN {self.COUN};TIM {self.TIM};BYP {self.BYP};DEL {self.DEL}"
        )

    def set_sensor(self):
        #             ":SENS1:CURR:RANG 0.002000;RANG:AUTO OFF;AUTO:ULIM 0.020000;LLIM 0.0001"

        self.write_and_log(
            f':SENS1:CHAR:APER {self.APER};APER:AUTO {self.APER_AUTO};AUTO:MODE LONG;'
        )
        if self.RANG_AUTO == "ON":
            self.write_and_log(
                f":SENS1:CURR:RANG:AUTO {self.RANG_AUTO};AUTO:ULIM {self.AUTO_ULIM};LLIM {self.AUTO_LLIM}"
            )
        else:
            self.write_and_log(
                f":SENS1:CURR:RANG {self.RANG};RANG:AUTO {self.RANG_AUTO}"
            )

        # test
        self.write_and_log(":SENS1:CURR:RANG 2.000000E-6;RANG:AUTO ON;AUTO:ULIM 100e-9;LLIM 1e-16")

    def enable_io(self):
        self.write_and_log(":OUTP1 ON;")
        self.write_and_log(":INP1 ON;")

    def turn_off_io(self):
        self.write_and_log(":OUTP1 OFF;")
        self.write_and_log(":INP1 OFF;")

    def connect_to_keysight_em(self, ip="192.168.113.72") -> TCPIPSocket:
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
        if not os.path.isfile(self.filename):
            logger.warning("File does not exist, data not saved")
            return

        with open(self.filename, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # remove overflow values from the data
            current_array = np.array(self.current_list, dtype=float)
            indexes = np.where(current_array < OVERFLOW_UPPER_LIMIT)
            cl = np.array(self.current_list)[indexes]
            tl = np.array(self.time_list)[indexes]
            writer.writerows(zip(tl, cl))

        self.time_list.clear()
        self.current_list.clear()

    def get_trigger_based_data(self, start_time: float = 0):
        times = self.my_instrument.query(":FETCH:ARR:TIME? (@1);")
        cur = self.my_instrument.query(":FETCH:ARR:CURR? (@1);")
        time_list = times.split(",")
        current_list = cur.split(",")
        try:
            time_arr = np.array(time_list, dtype=float) + start_time
            self.time_list = time_arr.tolist() # type: ignore
            self.current_list = current_list
            self.save_data_to_file()
            self.turn_off_io()
        except Exception as e:
            logger.error("Error in converting data to float: %s", e)

    def query_and_log(self, command: str):
        try:
            response = self.my_instrument.query(command)
            if command.startswith(":STAT"):
                logger.info(
                    "Query to EM: %s -> Response: %s",
                    command,
                    f"0b{int(response):016b}",
                )
            else:
                logger.info("Query to EM: %s -> Response: %s", command, response)

            error_request = self.my_instrument.query("SYST:ERR?")
            if error_request != '+0,"No error"':
                logger.error("Error: %s", error_request)
            return response
        except pyvisa.errors.VisaIOError as e:
            logger.error("Query: %s -> Error: %s", command, e)
            return str(e)

    def write_and_log(self, command: str):
        try:
            self.my_instrument.write(command)
            logger.info("Write to EM: %s", command)
            error_request = self.my_instrument.query("SYST:ERR?")
            if error_request != '+0,"No error"':
                logger.error("Error: %s", error_request)
                self.write_and_log("*CLS")
        except pyvisa.errors.VisaIOError as e:
            logger.error("Write: %s -> Error: %s", command, e)
