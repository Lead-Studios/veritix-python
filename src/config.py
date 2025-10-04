# src/config.py
from pydantic import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

# Load .env in development only
load_dotenv(override=False)

class Settings(BaseSettings):
    # Expect full PEM strings (including header/footer)
    PRIVATE_KEY_PEM: Optional[str] = None
    PUBLIC_KEY_PEM: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # prevent pydantic from ever printing values in exceptions
        keep_untouched = (os.environ,)

# global settings instance
settings = Settings()
