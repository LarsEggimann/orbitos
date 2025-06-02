import os
from typing import Literal


class Config:
    """Settings for the application."""

    # Application settings
    PROJECT_NAME: str = "ORBITOS API"
    API_V1_STR: str = "/orbitos-api/v1"

    # Database settings
    SQLITE_FILEPATH: str = os.path.join(
        os.path.dirname(__file__), "orbitos-api-core.db"
    )
    SQLITE_URL: str = f"sqlite:///{SQLITE_FILEPATH}"

    # CORS settings
    CORS_ORIGINS: list[str] | str | None = None

    # Sensitive settings
    ENVIRONMENT: Literal["local", "development", "production"] = "development"


    HEALTH_CHECK_INTERVAL: int = 30  # seconds


config: Config = Config()  # type: ignore
