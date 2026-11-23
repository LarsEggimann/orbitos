import logging

from src.shared.websocket_manager import WebSocketManager
from src.shared.state_manager import StateManager

from .relay import Relay
from ..models import PandoraState, RelayState

logger = logging.getLogger(__name__)


class RelaysController:
    def __init__(self, state: StateManager[PandoraState], ws_manager: WebSocketManager):

        self._relays: dict[int, Relay] = {
            0: Relay(io_pin=5, state=state),
            1: Relay(io_pin=6, state=state),
            2: Relay(io_pin=13, state=state),

            3: Relay(io_pin=19, state=state),
            4: Relay(io_pin=26, state=state),
            5: Relay(io_pin=21, state=state),
        }

        self.ws_manager = ws_manager
        self.state = state


        # add relays to the state
        relay_dict = self.state.get().relays
        for relay_id, relay in self._relays.items():
            if relay_id not in relay_dict:
                relay_dict[relay_id] = RelayState(
                    is_on=relay.is_on(),
                    description=f"Relay {relay_id} on GPIO pin {relay._gpio.pin}"
                )


        try:
            self.update_relays_state()
        except Exception as e:
            logger.error("Error updating relays state during initialization: %s", e)

    def get_relay(self, relay_id: int) -> Relay:
        if relay_id not in self._relays:
            raise ValueError(f"Relay with ID {relay_id} not found.")
        return self._relays[relay_id]

    def turn_on_relay(self, relay_id: int):
        relay = self.get_relay(relay_id)
        relay.on()
        self.state.get().relays[relay_id].is_on = True
        self.state.update()

    def turn_off_relay(self, relay_id: int):
        relay = self.get_relay(relay_id)
        relay.off()
        self.state.get().relays[relay_id].is_on = False
        self.state.update()

    def update_relays_state(self):
        """
        Update the state of all relays in the PandoraState model.
        This method should be called after any relay state change to ensure
        that the state is consistent with the actual hardware state.
        """
        for relay_id, relay in self._relays.items():
            self.state.get().relays[relay_id].is_on = relay.is_on()
        

