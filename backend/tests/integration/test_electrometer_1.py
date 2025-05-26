import logging
import time
from tests.conftest import ClientHelper

logger = logging.getLogger()

test_device_id = "electrometer_1"
test_electrometer_ip = "192.168.113.72"

def test_connect_to_electrometer(client_helper: ClientHelper):
    # First disconnect to test fresh connection
    try:
        client_helper.request(
            route_name="disconnect_electrometer",
            method="post",
            path_params={"device_id": test_device_id},
        )
    except:
        pass  # Ignore if already disconnected
    
    response = client_helper.request(
        route_name="connect_to_electrometer",
        method="post",
        path_params={"device_id": test_device_id, "ip": test_electrometer_ip},
    )
    
    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    assert "Connected to" in data["message"]
    assert test_device_id in data["message"]
    assert test_electrometer_ip in data["message"]


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


def test_start_continuous_measurement(client_helper: ClientHelper):
    response = client_helper.request(
        route_name="start_continuous_measurement",
        method="post",
        path_params={"device_id": test_device_id},
    )

    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    assert "message" in data
    
    # Let it run briefly to collect some data
    time.sleep(5)


def test_stop_continuous_measurement(client_helper: ClientHelper):
    
    response = client_helper.request(
        route_name="stop_continuous_measurement",
        method="post",
        path_params={"device_id": test_device_id},
    )

    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    assert "message" in data


def test_initialize_trigger_based_measurement(client_helper: ClientHelper):
    response = client_helper.request(
        route_name="initialize_trigger_based_measurement",
        method="post",
        path_params={"device_id": test_device_id},
    )

    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    assert "message" in data


def test_start_trigger_based_measurement(client_helper: ClientHelper):
    # Initialize first
    client_helper.request(
        route_name="initialize_trigger_based_measurement",
        method="post",
        path_params={"device_id": test_device_id},
    )
    time.sleep(1)
    
    response = client_helper.request(
        route_name="start_trigger_based_measurement",
        method="post",
        path_params={"device_id": test_device_id},
    )

    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    assert "message" in data
    
    # Wait for measurement to complete
    time.sleep(3)


def test_get_current_data_no_params(client_helper: ClientHelper):
    # Ensure we have some data by running a quick measurement
    client_helper.request(
        route_name="start_continuous_measurement",
        method="post",
        path_params={"device_id": test_device_id},
    )
    time.sleep(2)
    client_helper.request(
        route_name="stop_continuous_measurement",
        method="post",
        path_params={"device_id": test_device_id},
    )
    
    response = client_helper.request(
        route_name="get_current_data",
        method="get",
        path_params={"device_id": test_device_id},
    )

    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    
    assert "device_id" in data
    assert data["device_id"] == test_device_id
    assert "current" in data
    assert "time" in data
    assert isinstance(data["current"], list)
    assert isinstance(data["time"], list)


def test_get_current_data_with_time_frame(client_helper: ClientHelper):
    response = client_helper.request(
        route_name="get_current_data",
        method="get",
        path_params={"device_id": test_device_id},
        query_params={
            "start": "2024-01-01T00:00:00Z",
            "end": "2025-12-31T23:59:59Z"
        }
    )

    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    
    assert "device_id" in data
    assert data["device_id"] == test_device_id
    assert "current" in data
    assert "time" in data
    assert isinstance(data["current"], list)
    assert isinstance(data["time"], list)


def test_disconnect_electrometer(client_helper: ClientHelper):
    # Ensure we're connected first
    client_helper.request(
        route_name="connect_to_electrometer",
        method="post",
        path_params={"device_id": test_device_id, "ip": test_electrometer_ip},
    )
    time.sleep(1)
    
    response = client_helper.request(
        route_name="disconnect_electrometer",
        method="post",
        path_params={"device_id": test_device_id},
    )

    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    assert "Disconnected from" in data["message"]
    assert test_device_id in data["message"]

    # Verify disconnection by checking state
    state_response = client_helper.request(
        route_name="get_electrometer_state",
        method="get",
        path_params={"device_id": test_device_id},
    )
    assert state_response.status_code == 200
    state_data = state_response.json()
    assert state_data["connection_status"] == "disconnected"


def test_reset_electrometer(client_helper: ClientHelper):
    response = client_helper.request(
        route_name="reset_electrometer",
        method="post",
    )

    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    assert "All electrometers have been reset" in data["message"]

    # After reset, device should be disconnected
    time.sleep(1)
    state_response = client_helper.request(
        route_name="get_electrometer_state",
        method="get",
        path_params={"device_id": test_device_id},
    )
    assert state_response.status_code == 200
    state_data = state_response.json()
    assert state_data["connection_status"] == "disconnected"


def test_disconnect_when_not_connected_should_fail(client_helper: ClientHelper):
    # Ensure disconnected first
    try:
        client_helper.request(
            route_name="disconnect_electrometer",
            method="post",
            path_params={"device_id": test_device_id},
        )
    except:
        pass
    
    # Try to disconnect again - should fail
    response = client_helper.request(
        route_name="disconnect_electrometer",
        method="post",
        path_params={"device_id": test_device_id},
    )

    assert response.status_code == 400, "Should fail when not connected"
    assert "not connected" in response.json()["detail"]
