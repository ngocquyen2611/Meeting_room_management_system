from typing import List, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5433/meeting_room"
    )

    # Auth0
    AUTH0_DOMAIN: str = "dev-example.us.auth0.com"
    AUTH0_AUDIENCE: str = "https://meeting-room-api"
    AUTH0_ALGORITHMS: str = "RS256"

    # Application
    ENVIRONMENT: str = "development"
    PORT: int = 8001
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def auth0_issuer(self) -> str:
        domain = self.AUTH0_DOMAIN.strip("/")
        return f"https://{domain}/"

    @property
    def auth0_jwks_url(self) -> str:
        return f"{self.auth0_issuer}.well-known/jwks.json"


settings = Settings()
