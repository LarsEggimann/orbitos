import logging
import serial
from dataclasses import dataclass
import numpy as np

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
        Converts the incoming thermistor ADC value to a temperature based on claibration
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


    def fetch_temperature(self):
        """
        Fetch the temperature from the arduino and update the state.
        """
        try:
                #             line = context["ser"].readline().decode('utf-8').strip()
                # tp_notsynch, pt = map(float, line.split()[1::3])
                # tp_buf.append(tp_notsynch)
                # if len(tp_buf) < (lag + 1):
                #     continue
                # tp = tp_buf[0]
                # if tp <= const["thermopile"]["tp_min"]:
                #     continue
                # if getline is True:
                #     PT = convertPTtoK(pt,const)
                #     TP = convertTPtoK(tp,PT,const)
                #     print(f"ambient temperature: {PT}, object temperatur: {TP}")
            line = self.serial_connection.readline().decode('utf-8').strip()
            tp_notsynch, pt = map(float, line.split()[1::3])
            if tp_notsynch <= self.thermopile_calibration.tp_min:
                logger.warning("Thermopile reading below minimum threshold: %f", tp_notsynch)
                return
            PT = self.thermistor_calibration.convert_PT_to_K(pt)
            TP = self.thermopile_calibration.convert_TP_to_K(tp_notsynch, PT)
            self.state.get().temperature_sensor.ambient_temperature = PT - 273.15  # convert to Celsius
            self.state.get().temperature_sensor.object_temperature  = TP - 273.15  # convert to Celsius
            self.state.update()

            # debugging print
            # print(f"ambient temperature: {PT - 273.15:.2f} °C, object temperature: {TP - 273.15:.2f} °C")

            return self.state.get().temperature_sensor.ambient_temperature, self.state.get().temperature_sensor.object_temperature

        except Exception as e:
            logger.error("Error fetching temperature: %s", e)

