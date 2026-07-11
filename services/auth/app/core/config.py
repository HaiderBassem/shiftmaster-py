"""
Application configuration using pydantic-settings.

All settings are loaded from environment variables (with optional .env file).
No sensitive default values are provided — missing required values cause an
explicit startup failure with a clear error message, not a silent security
hole.

Environment variable naming convention:
    Section prefix + field name → e.g. DB_HOST, JWT_SECRET, REDIS_URL
"""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


# ── Database ──────────────────────────────────────────────────────────────────

class DatabaseSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    user: str = "shift_py"
    # No default password — MUST be provided via environment
    password: str = Field(..., min_length=1)
    name: str = "shift_master_py_db"
    ssl_mode: str = "disable"
    max_open_conns: int = 50
    min_conns: int = 10

    model_config = {"env_prefix": "DB_"}

    @property
    def url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
            f"?sslmode={self.ssl_mode}"
        )


# ── JWT ───────────────────────────────────────────────────────────────────────

class JWTSettings(BaseSettings):
    # MUST be provided — minimum 32 chars enforced
    secret: str = Field(..., min_length=32)
    issuer: str = "shiftmaster-py"
    access_expire_min: int = 15
    refresh_expire_days: int = 7
    bcrypt_cost: int = 12

    model_config = {"env_prefix": "JWT_"}


# ── Server ────────────────────────────────────────────────────────────────────

class ServerSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8001
    env: str = "development"
    workers: int = 1

    model_config = {"env_prefix": "SERVER_"}

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        return self.env == "development"


# ── CORS ──────────────────────────────────────────────────────────────────────

class CORSSettings(BaseSettings):
    allowed_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_prefix": "CORS_"}


# ── Uploads ───────────────────────────────────────────────────────────────────

class UploadSettings(BaseSettings):
    base_path: str = "./uploads"
    max_file_size_mb: int = 5

    model_config = {"env_prefix": "UPLOAD_"}

    @property
    def max_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


# ── Redis ─────────────────────────────────────────────────────────────────────

class RedisSettings(BaseSettings):
    url: str = "redis://localhost:6379/0"
    # Rate-limiting defaults (can be overridden per-endpoint)
    login_max_attempts: int = 5
    login_window_seconds: int = 300   # 5 minutes

    model_config = {"env_prefix": "REDIS_"}


# ── RabbitMQ ──────────────────────────────────────────────────────────────────

class RabbitMQSettings(BaseSettings):
    url: str = "amqp://guest:guest@localhost:5672/"
    user: str = "guest"
    password: str = "guest"

    model_config = {"env_prefix": "RABBITMQ_"}


# ── Root settings ─────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    project_name: str = "Shiftmaster-py"
    api_v1_str: str = "/api/v1"

    db: DatabaseSettings = DatabaseSettings()          # type: ignore[call-arg]
    jwt: JWTSettings = JWTSettings()                   # type: ignore[call-arg]
    server: ServerSettings = ServerSettings()
    cors: CORSSettings = CORSSettings()
    upload: UploadSettings = UploadSettings()
    redis: RedisSettings = RedisSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()


settings = Settings()  # type: ignore[call-arg]