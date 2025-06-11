import os
import secrets

from cryptography.fernet import Fernet
from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

env_file = os.path.join(os.path.dirname(__file__), ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_file,
        env_ignore_empty=True,
        extra="ignore",
        env_file_encoding="utf-8",
    )

    # General settings
    app_name: str = "AutoFlowBot"
    app_version: str = "1.0.0"
    app_description: str = "An AI-powered workflow automation assistant"
    GEMINI_API_KEY: str
    ENCRYPTION_KEY: str = Fernet.generate_key().decode()
