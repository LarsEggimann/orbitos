import logging
from fastapi.testclient import TestClient
from src.core.config import config

logger = logging.getLogger()

test_device_id = "electrometer_1"
test_electrometer_ip = "192.168.113.72"


def test_connect_to_electrometer_success(
    client: TestClient
):
    response = client.post(
        f"{config.API_V1_STR}/{test_device_id}/connect/{test_electrometer_ip}"
    ) 
    assert response.status_code == 200, f"Error: {response.text}"


def test_get_electrometer_state(
    client: TestClient
):
    response = client.post(
        f"{config.API_V1_STR}/{test_device_id}/connect/{test_electrometer_ip}"
    ) 
    data = response.json()
    
    assert response.status_code == 200, f"Error: {response.text}"
    assert isinstance(data, dict), "State should be a dictionary"
    assert "device_id" in data, "State should contain 'device_id'"
    assert data["device_id"] == test_device_id, "Device ID in state does not match expected"
