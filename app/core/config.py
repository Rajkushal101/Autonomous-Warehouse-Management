import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development")
    PORT: int = Field(default=8080)
    HOST: str = Field(default="127.0.0.1")
    LOG_LEVEL: str = Field(default="INFO")

    # Database
    DATABASE_URL: str = Field(default="sqlite:///./warehouse_dev.db")

    # Cryptography & Security
    SESSION_SECRET_KEY: str = Field(default="change-this-secret-key-in-production-use-a-strong-64-char-random-key")
    CSRF_SECRET_KEY: str = Field(default="change-this-csrf-secret-key-in-production-use-a-strong-random-key")
    DEVICE_TOKEN_PEPPER: str = Field(default="change-this-device-pepper-key-in-production-use-strong-random")

    # Session Timeouts
    SESSION_LIFETIME_SECONDS: int = Field(default=1800)  # 30 minutes
    SESSION_IDLE_TIMEOUT_SECONDS: int = Field(default=600)  # 10 minutes
    SECURE_COOKIES: bool = Field(default=False)

    # Simulator
    SIMULATOR_TICK_RATE_MS: int = Field(default=500)
    ROBOT_HEARTBEAT_TIMEOUT_SECONDS: int = Field(default=30)
    WAREHOUSE_ID: str = Field(default="11111111-1111-1111-1111-111111111111")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
