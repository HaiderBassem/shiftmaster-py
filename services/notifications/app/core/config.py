"""
Application configuration using pydantic-settings.

All settings are loaded from environment variables (with optional .env file).
No sensitive default values are provided — missing required values cause an
explicit startup failure with a clear error message, not a silent security
hole.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    user: str = "shift_py"
    password: str = Field(..., min_length=1)
    name: str = "shift_master_py_db"
    ssl_mode: str = "disable"
    max_open_conns: int = 15
    min_conns: int = 10

    model_config = {"env_prefix": "DB_"}

    @property
    def url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
            f"?sslmode={self.ssl_mode}"
        )

class ServerSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8003
    env: str = "development"
    workers: int = 1

    model_config = {"env_prefix": "SERVER_"}

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        return self.env == "development"

class CORSSettings(BaseSettings):
    allowed_origins: list[str] = ["*"]
    model_config = {"env_prefix": "CORS_"}

class RabbitMQSettings(BaseSettings):
    url: str = "amqp://guest:guest@localhost:5672/"
    user: str = "guest"
    password: str = "guest"
    model_config = {"env_prefix": "RABBITMQ_"}

class RedisSettings(BaseSettings):
    url: str = "redis://localhost:6379/0"
    model_config = {"env_prefix": "REDIS_"}

class Settings(BaseSettings):
    project_name: str = "Shiftmaster-py Notifications Service"
    api_v1_str: str = "/api/v1"

    db: DatabaseSettings = DatabaseSettings()          # type: ignore[call-arg]
    server: ServerSettings = ServerSettings()
    cors: CORSSettings = CORSSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    redis: RedisSettings = RedisSettings()

settings = Settings()  # type: ignore[call-arg]
