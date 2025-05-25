from typing import Generator, Dict, Any
from httpx import Response
import pytest
from fastapi.testclient import TestClient
from fastapi.routing import APIRoute

from src.main import app

class ClientHelper:
    def __init__(self, test_client: TestClient, routes: Dict[str, str]):
        self.client = test_client
        self.routes = routes

    def format_route(self, route_name: str, **kwargs: Any) -> str:
        path_template = self.routes.get(route_name)
        if not path_template:
            raise ValueError(f"Route '{route_name}' not found in route map")
        try:
            return path_template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing path parameter '{e.args[0]}' for route: {path_template}") from e

    def request(
        self,
        method: str,
        route_name: str,
        *,
        path_params: dict[str, Any] = {},
        query_params: dict[str, Any] = {},
        json: Any = None,
        headers: dict[str, str] = {},
    ) -> Response:
        """
        Make a request using the FastAPI TestClient.
        """
        path = self.format_route(route_name, **path_params)
        return self.client.request(
            method=method,
            url=path,
            params=query_params,
            json=json,
            headers=headers
        )

@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """
    Provides a TestClient instance for making requests to the FastAPI application.
    The app's lifespan manager (including module init/shutdown) will be used.
    """
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="session")
def route_map() -> Dict[str, str]:
    """
    Create a dictionary mapping endpoint names or operation IDs to their paths.
    This helps avoid hardcoding URLs in tests.
    """
    routes = {}
    for route in app.routes:
        if isinstance(route, APIRoute):
            # Use operation_id or name as key; adjust as needed
            operation_id = route.operation_id or route.name
            routes[operation_id] = route.path

    return routes

@pytest.fixture(scope="session")
def client_helper(client: TestClient, route_map: Dict[str, str]) -> ClientHelper:
    return ClientHelper(test_client=client, routes=route_map)
