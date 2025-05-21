from typing import Literal

class Config():
    """Settings for the application."""

    # Application settings
    PROJECT_NAME: str = "ORBITOS API"
    API_V1_STR: str = "/orbitos-api/v1"

    # Database settings
    SQLITE_FILENAME: str = "app.db"
    SQLITE_URL: str = f"sqlite:///{SQLITE_FILENAME}"


    # CORS settings
    CORS_ORIGINS: list[str] | str | None = None

    # Sensitive settings
    ENVIRONMENT: Literal["local", "development", "production"] = "development"


config: Config = Config()  # type: ignore
