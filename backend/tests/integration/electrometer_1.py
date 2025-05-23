import pytest
from fastapi.testclient import TestClient
from src.core.config import config
from src.modules.electrometer.models import ElectrometerState # For type hinting or asserting structure

# Assuming your API prefix from config.API_V1_STR is "/api/v1"
API_PREFIX = "/api/v1" # Or fetch from src.core.config.config.API_V1_STR

@pytest.mark.asyncio
async def test_connect_to_electrometer_success(
    client: TestClient, 
    test_device_id: str, 
    test_electrometer_ip: str
):
    """
    Tests successful connection to an electrometer.
    This test assumes a real electrometer is available at test_electrometer_ip.
    """
    response = client.post(
        f"{config.API_V1_STR}/{test_device_id}/connect/{test_electrometer_ip}"
    )
    
    assert response.status_code == 200, f"Error: {response.text}"
    
    data = response.json()
    
    assert data["device_id"] == test_device_id
