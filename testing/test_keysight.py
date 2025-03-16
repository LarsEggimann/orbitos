#!/usr/bin/python

import os

import numpy as np
import pyvisa
from pyvisa.resources import TCPIPSocket


def write_and_log(command: str):
    try:
        my_instrument.write(command)
        print(f"Write to EM: {command}")
        error_request = my_instrument.query("SYST:ERR?")
        if error_request != '+0,"No error"':
            print(f"Error: {error_request}")
    except pyvisa.errors.VisaIOError as e:
        print(f"Write: {command} -> Error: {e}")


def query_and_log(command: str):
    try:
        response = my_instrument.query(command)
        if command.startswith(":STAT"):
            print(f"Query to EM: {command} -> Response: 0b{int(response):016b}")
        else:
            print(f"Query to EM: {command} -> Response: {response}")

        error_request = my_instrument.query("SYST:ERR?")
        if error_request != '+0,"No error"':
            print("Error: %s", error_request)
        return response
    except pyvisa.errors.VisaIOError as e:
        print("Query: %s -> Error: %s", command, e)
        return str(e)


rm = pyvisa.ResourceManager("@py")

my_instrument: TCPIPSocket = rm.open_resource("TCPIP::192.168.113.72::5025::SOCKET")

if my_instrument.resource_name.startswith(
    "ASRL"
) or my_instrument.resource_name.endswith("SOCKET"):
    my_instrument.read_termination = "\n"

print("Connected!")

print("Pinging...")
os.system("ping -c 1 192.168.113.72")

print("Querying...")

write_and_log("*RST")
write_and_log(":FORM ASC;:FORM:DIG ASC;:FORM:ELEM:CALC CALC,TIME,STAT;:FORM:SREG ASC;")
write_and_log(':SENS1:FUNC "CURR",;')
write_and_log(":OUTP1:LOW COMM;:OUTP1:OFF:MODE ZERO;")
write_and_log(":SOUR1:FUNC:MODE VOLT;:SOUR1:FUNC:TRIG:CONT OFF;:SOUR1:VOLT:TRIG 0.000")
write_and_log(":SENS1:CURR:APER 0.000200;APER:AUTO OFF;AUTO:MODE LONG;")
write_and_log(":SENS1:CURR:RANG 0.002000;RANG:AUTO OFF;AUTO:ULIM 0.020000;LLIM 0.0001")
write_and_log(":TRIG1:ALL:SOUR TIM;DEL 0.000000;COUN 100;TIM 0.001;BYP OFF")
write_and_log(":OUTP1 ON;")
write_and_log(":INP1 ON;")

write_and_log(":INIT:ALL (@1);")
total_list = []
# Continuous measurement loop
try:
    while True:
        # time.sleep(0.001)  # Adjust the sleep time as needed
        cur = my_instrument.query(":READ:ARR:CURR? (@1);")
        current_list = np.array(cur.split(",")).astype(float)
        print(current_list)
        total_list.extend(current_list)

        print(f"Current data: {len(total_list)}")

        # Optional: process the current_data here
        # e.g., save to a file, plot in real-time, etc.

except KeyboardInterrupt:
    print("Measurement stopped by user.")

finally:
    write_and_log(":OUTP1 OFF;")
    write_and_log(":INP1 OFF;")
    my_instrument.close()
    rm.close()
    print("Instrument closed.")
    print(total_list)
