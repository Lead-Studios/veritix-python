from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    QR_SIGNING_KEY: str = Field(..., min_length=32)
    DATABASE_URL: str
    NEST_API_BASE_URL: str
    NEST_API_TOKEN: Optional[str] = None
    ENABLE_ETL_SCHEDULER: bool = False
    ETL_CRON: Optional[str] = None
    ETL_INTERVAL_MINUTES: int = 15
    DEBUG: bool = False
    BQ_ENABLED: bool = False
    BQ_PROJECT_ID: Optional[str] = None
    BQ_DATASET: Optional[str] = None
    BQ_LOCATION: Optional[str] = None

    # Existing project configuration values kept centralized.
    PRIVATE_KEY_PEM: Optional[str] = None
    PUBLIC_KEY_PEM: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    SESSION_TIMEOUT_MINUTES: int = 30
    SKIP_MODEL_TRAINING: bool = False
    BQ_TABLE_EVENT_SUMMARY: str = "event_sales_summary"
    BQ_TABLE_DAILY_SALES: str = "daily_ticket_sales"

   
    POOL_SIZE: int = 5
    POOL_MAX_OVERFLOW: int = 10
    REPORT_CACHE_MINUTES: int = 60
    SHUTDOWN_TIMEOUT_SECONDS: int = 30

    SERVICE_API_KEY: str = Field(...)
    ADMIN_API_KEY: str = Field(...)

    @field_validator("SERVICE_API_KEY", "ADMIN_API_KEY")
    @classmethod
    def validate_api_keys(cls, v: str, info) -> str:
        forbidden = {"default_service_secret_change_me", "default_admin_secret_change_me"}
        if v in forbidden or len(v) < 32:
            raise ValueError(
                f"{info.field_name} must be at least 32 characters and must not use a default value"
            )
        return v
    KNOWN_LOCATIONS: str = (
        "lagos,abuja,port harcourt,kano,ibadan,benin,kaduna,jos,enugu,calabar,"
        "owerri,warri,uyo,akure,ilorin,sokoto,zaria,maiduguri,asaba,nnewi"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
