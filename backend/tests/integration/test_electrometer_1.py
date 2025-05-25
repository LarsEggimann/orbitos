import logging

from tests.conftest import ClientHelper

logger = logging.getLogger()

test_device_id = "electrometer_1"
test_electrometer_ip = "192.168.113.72"


def test_connect_to_electrometer_success(client_helper: ClientHelper):
    response = client_helper.request(
        route_name="connect_to_electrometer",
        method="post",
        path_params={"device_id": test_device_id, "ip": test_electrometer_ip},
    )

    assert response.status_code == 200, f"Error: {response.text}"


def test_get_electrometer_state(client_helper: ClientHelper):
    response = client_helper.request(
        route_name="get_electrometer_state",
        method="get",
        path_params={"device_id": test_device_id},
    )

    assert response.status_code == 200, f"Error: {response.text}"

    data = response.json()

    assert isinstance(data, dict), "State should be a dictionary"
    assert "device_id" in data, "State should contain 'device_id'"
    assert data["device_id"] == test_device_id, (
        "Device ID in state does not match expected"
    )
    assert "connection_status" in data, "State should contain 'connection_status'"
    assert data["connection_status"] == "connected", (
        "Connection status should be 'connected'"
    )
