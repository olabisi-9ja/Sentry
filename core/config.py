import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    
    class Settings(BaseSettings):
        APP_NAME: str = "Sentry"
        DEBUG: bool = False
        ADMIN_PASSCODE: str = "sentry_admin_passcode"
        META_WA_VERIFY_TOKEN: str = "sentry_kwasu_secret_2026"
        SECURITY_STAFF_WHATSAPP_NUMBER: Optional[str] = None
        WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
        WHATSAPP_ACCESS_TOKEN: Optional[str] = None
        DATABASE_URL: Optional[str] = None
        GEMINI_API_KEY: Optional[str] = None
        OLLAMA_BASE_URL: Optional[str] = None
        OLLAMA_MODEL: Optional[str] = None
        USE_OLLAMA: str = "false"

        model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    settings = Settings()

except ImportError:
    from pydantic import BaseModel

    class Settings(BaseModel):
        APP_NAME: str = os.getenv("APP_NAME", "Sentry")
        DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
        ADMIN_PASSCODE: str = os.getenv("ADMIN_PASSCODE", "sentry_admin_passcode")
        META_WA_VERIFY_TOKEN: str = os.getenv("META_WA_VERIFY_TOKEN", "sentry_kwasu_secret_2026")
        SECURITY_STAFF_WHATSAPP_NUMBER: Optional[str] = os.getenv("SECURITY_STAFF_WHATSAPP_NUMBER")
        WHATSAPP_PHONE_NUMBER_ID: Optional[str] = os.getenv("META_WA_PHONE_NUMBER_ID")
        WHATSAPP_ACCESS_TOKEN: Optional[str] = os.getenv("META_WA_ACCESS_TOKEN")
        DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
        GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
        OLLAMA_BASE_URL: Optional[str] = os.getenv("OLLAMA_BASE_URL")
        OLLAMA_MODEL: Optional[str] = os.getenv("OLLAMA_MODEL")
        USE_OLLAMA: str = os.getenv("USE_OLLAMA", "false")

    settings = Settings()
