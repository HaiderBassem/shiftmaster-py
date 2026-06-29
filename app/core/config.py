from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class DatabaseSettings(BaseSettings):

    host: str = "localhost"
    port: int = 5432
    user: str = "shift_py"
    password: str = "thisistest"
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


class JWTSettings(BaseSettings):
    secret: str = Field(min_length=32)
    issuer: str = "shiftmaster-py"
    access_expire_min: int = 15
    refresh_expire_days: int = 7
    bcrypt_cost: int = 12

    model_config = {"env_prefix": "JWT_"}


class ServerSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8080
    env: str = "development"

    model_config = {"env_prefix": "SERVER_"}

    @property
    def is_production(self) -> bool:
        return self.env == "production"


class CORSSettings(BaseSettings):
    allowed_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_prefix": "CORS_"}


class UploadSettings(BaseSettings):
    base_path: str = "./uploads"
    max_file_size_mb: int = 5

    model_config = {"env_prefix": "UPLOAD_"}

    @property
    def max_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


class Settings(BaseSettings):
    project_name: str = "Shiftmaster-py"
    api_v1_str: str = "/api/v1"
    db: DatabaseSettings = DatabaseSettings()
    jwt: JWTSettings = JWTSettings()
    server: ServerSettings = ServerSettings()
    cors: CORSSettings = CORSSettings()
    upload: UploadSettings = UploadSettings()



settings = Settings()