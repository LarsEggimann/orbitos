import secrets
from typing import Literal

class Settings():
    """Settings for the application."""

    # Application settings
    PROJECT_NAME: str = "FastAPI Template"
    API_V1_STR: str = "/api/v1"

    # Database settings
    SQLITE_FILENAME: str = "app.db"
    SQLITE_URL: str = f"sqlite:///{SQLITE_FILENAME}"

    # Security settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 1  # 1 day

    # CORS settings
    CORS_ORIGINS: list[str] | str | None = None

    # Sensitive settings
    ENVIRONMENT: Literal["local", "development", "production"] = "local"


settings: Settings = Settings()  # type: ignore
