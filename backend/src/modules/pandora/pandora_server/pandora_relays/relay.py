import logging

from src.shared.state_manager import StateManager

from ..models import PandoraState

logger = logging.getLogger(__name__)

# this is a bit a hacky way to handle the fact that we might not be running on a Raspberry Pi and thus don't have access to the GPIO pins
# so I just try to create an OutputDevice and if that fails I use a MockFactory to mock the GPIO pins, this way at least the API starts up
try:
    from gpiozero import OutputDevice
    OutputDevice(1)  # test if gpiozero is available
except ImportError:
    from gpiozero.pins.mock import MockFactory
    from gpiozero import Device, OutputDevice

    Device.pin_factory = MockFactory()


class Relay():
    def __init__(self, io_pin: int, state: StateManager[PandoraState]):
        self._gpio = OutputDevice(io_pin, active_high=True) # active_high=True means that when we do .on() the relay will switch to HIGH
        self.state = state

    def on(self):
        self._gpio.on()

    def off(self):
        self._gpio.off()

    def is_on(self) -> bool:
        return self._gpio.is_active
