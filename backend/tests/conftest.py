import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from typing import AsyncGenerator

# Import your FastAPI app
from src.main import app
# Import your electrometer module (for direct device interaction if needed for setup/teardown)
from src.core.config import config
from src.modules.electrometer import module as electrometer_module
from src.modules.electrometer.controller import KeysightEM # Assuming this is your actual controller class
from src.modules.electrometer.models import ElectrometerState

# Configuration for your test electrometer
# IMPORTANT: Replace with your actual device IP and ID for testing!
TEST_ELECTROMETER_IP = "192.168.113.72"
TEST_ELECTROMETER_ID = "electrometer_1"


@pytest.fixture(scope="session") # "session" scope means this fixture runs once per test session
def client() -> TestClient:
    """
    Provides a TestClient instance for making requests to the FastAPI application.
    The app's lifespan manager (including module init/shutdown) will be used.
    """
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="session")
async def connect_to_electrometer_1_for_tests() -> str:
    """
    Fixture to manage the lifecycle of a real electrometer device for testing.
    This simulates connecting/disconnecting the electrometer before/after tests.
    The 'session' scope ensures the physical connection is made only once.
    """
    print(f"\nAttempting to connect to electrometer {TEST_ELECTROMETER_ID} at {TEST_ELECTROMETER_IP} for tests...")

    try:
        response = client().post(
            f"{config.API_V1_STR}/{TEST_ELECTROMETER_ID}/connect/{TEST_ELECTROMETER_IP}"
        )
        print(f"Successfully connected electrometer for tests: {response}")
        yield "initialized"

    except Exception as e:
        pytest.fail(f"Could not connect to the real electrometer at {TEST_ELECTROMETER_IP}. "
                     "Please ensure the device is powered on, connected, and the IP is correct. "
                     f"Error: {e}")
    finally:
        print(f"\nDisconnecting electrometer from tests...")
        try:
            # TODO: disconnect!
            print("Electrometer disconnected cleanly.")
        except Exception as e:
            print(f"Warning: Error during electrometer disconnect in fixture: {e}")
