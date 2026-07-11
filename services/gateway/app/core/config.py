from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    auth_service_url: str = "http://auth:8001"
    monolith_url: str = "http://monolith:8004"
    schedule_service_url: str = "http://schedule:8002"
    notification_service_url: str = "http://notifications:8003"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "supersecretjwtkeythatislongenough32chars"

    model_config = {"env_file": ".env"}

settings = Settings()
