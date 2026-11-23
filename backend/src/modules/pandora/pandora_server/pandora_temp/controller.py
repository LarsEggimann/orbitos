import logging
import serial
from dataclasses import dataclass
import numpy as np
import time

from src.shared.websocket_manager import WebSocketManager
from src.shared.state_manager import StateManager

from ..models import PandoraState, RelayState


logger = logging.getLogger(__name__)

# calibration data from Sascha:
@dataclass
class ThermopileCalibration:
    """
    The thermopile is based on boltzman stefan law: S(Vobj-Vamb)^4+c*Vamb+V0
    """
    S: float = 349.573
    c: float = 116.585
    V0: float = -17.1711
    V0_original: float = -17.1711
    tp_min: float = 50

    def convert_TP_to_K(self, TP, Tamb_K):
        """
        Converts the incoming thermopile ADC value and ambient temperature to a temperature that corresponds to the object temperature based on calibration
        """
        ta = Tamb_K / 300 # (chunnt vor kalibrierig, 300K ^4 isch riisig, drum /300, de sis chlineri zahle zum fitte)
        x = ta**4 + (TP - self.c*ta - self.V0) / self.S
        if x < 0: 
            return np.nan
        return 300 * x**0.25

@dataclass
class ThermistorCalibration:
    """
    The thermistor is based on steinhart-hart equation: 1/T = A + B*ln(R) + C*(ln(R))^3 + D*(ln(R))^5
    """
    A: float = 3.36281196e-03
    B: float = 2.63467301e-04
    C: float = 8.05881072e-06
    D: float = 1.41344239e-06

    def convert_PT_to_K(self, PT, full=1023):
        """
        Converts the incoming thermistor ADC value to a temperature based on calibration
        full is the full range, 1023 bits
        """
        if not 0 < PT < full: 
            return np.nan
        R = np.log(PT / (full - PT))
        OneOverT = self.A + self.B * R + self.C * (R**2) + self.D * (R**3)
        return 1 / OneOverT


class TemperatureReadoutController:
    def __init__(self, state: StateManager[PandoraState], ws_manager: WebSocketManager):

        self.ws_manager = ws_manager
        self.state = state

        self.thermistor_calibration = ThermistorCalibration()
        self.thermopile_calibration = ThermopileCalibration()

        # setup serial connection to arduino
        self.serial_port = "/dev/ttyACM0"  # hardcoded, should not change unless the hardware is changed

        try:
            self.serial_connection = serial.Serial(self.serial_port, baudrate=9600, timeout=1)
            logger.info("Connected to Temperature Readout Arduino on %s", self.serial_port)
        except serial.SerialException as e:
            logger.error("Failed to connect to Arduino on %s: %s", self.serial_port, e)
            self.serial_connection = None

    def _get_pt_and_tp(self):
        """
        Read the raw ADC values for the thermistor (PT) and thermopile (TP) from the Arduino.
        """
        debug_print = True
        try:
            line = self.serial_connection.readline().decode('utf-8').strip() # sould look something like "Thermopile 0 : Thermistor 441"

            if debug_print:
                logger.info(f"Raw Arduino string response: {line}")

            tp_notsynch, pt = map(float, line.split()[1::3]) # take every 3rd element starting from index 1, convert to float
            
            if debug_print:
                logger.info(f"Thermopile: {tp_notsynch}, Thermistor: {pt}")

            if tp_notsynch <= self.thermopile_calibration.tp_min:
                logger.info("Thermopile reading below minimum threshold: %f (threshold: %f)", tp_notsynch, self.thermopile_calibration.tp_min)
                return np.nan, np.nan

            PT = self.thermistor_calibration.convert_PT_to_K(pt)
            TP = self.thermopile_calibration.convert_TP_to_K(tp_notsynch, PT)

            return PT, TP

        except Exception as e:
            logger.error("Error reading temperature from Arduino: %s", e)
            return np.nan, np.nan


    def fetch_temperature(self):
        """
        Fetch the temperature from the arduino and update the state.
        """
        pt, tp = self._get_pt_and_tp()
        self.state.get().temperature_sensor.ambient_temperature = pt - 273.15  # convert to Celsius
        self.state.get().temperature_sensor.object_temperature  = tp - 273.15  # convert to Celsius
        self.state.update()
        return self.state.get().temperature_sensor.ambient_temperature, self.state.get().temperature_sensor.object_temperature

    def update_state(self):
        """
        Update the state of the temperature sensor in the PandoraState model.
        """
        self.fetch_temperature()  # This will update the state with the latest temperature readings

    def calibrate(self):
        """
        Calibrate the thermopile and thermistor based on current readings.
        This method should be called when the system is in a known stable temperature environment.
        """

        old_V0 = self.thermopile_calibration.V0
        calib_samples = 50
        calib_V0 = []

        for i in range(calib_samples):
            pt, tp = self._get_pt_and_tp()
            pt_norm = pt / 300  # normalization from saschas code, not sure why, but it seems to be necessary for the calibration to work properly
            calib_V0.append(tp - self.thermopile_calibration.c * pt_norm)
            # print on one line and remove line again to avoid flooding the log with too many lines
            print(f"Calibration sample {i+1}/{calib_samples}: Thermopile TP={tp:.4f}, Thermistor PT={pt:.4f}, V0_sample={calib_V0[-1]:.4f}", end='\r')
            time.sleep(0.01)  # very small delay between samples to not overwhelm the Arduino

        new_V0 = float(np.nanmean(calib_V0))
        if np.isfinite(new_V0):
            self.thermopile_calibration.V0 = round(new_V0, 4)
            logger.info("Calibration completed successfully. New V0: %f (old: %f)", self.thermopile_calibration.V0, old_V0)
        else:
            logger.error("Calibration failed. No valid samples were obtained (all NaN).")
