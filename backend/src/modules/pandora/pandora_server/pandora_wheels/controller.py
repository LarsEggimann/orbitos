

from src.shared.websocket_manager import WebSocketManager


class WheelsController:
    def __init__(self, ws_manager: WebSocketManager):

        self._wheels = dict(
            wheel_0=0,
            wheel_1=0,
            wheel_2=0,
            wheel_3=0,
        )

        self.ws_manager = ws_manager

    def go_to_position(self, wheel_id: int, angle_deg: float):
        """
        Move the wheel with the given ID to the specified angle in degrees.
        """
        print(f"Moving wheel {wheel_id} to position {angle_deg} degrees.")
        # TODO: implement the actual control logic to move the wheel to the desired position

