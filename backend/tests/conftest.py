from typing import Generator
import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture(scope="session") # "session" scope means this fixture runs once per test session
def client() -> Generator[TestClient, None, None]:
    """
    Provides a TestClient instance for making requests to the FastAPI application.
    The app's lifespan manager (including module init/shutdown) will be used.
    """
    print("Setting up TestClient for FastAPI application")
    with TestClient(app) as test_client:
        yield test_client
