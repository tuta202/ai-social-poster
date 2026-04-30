from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./postpilot.db"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h
    OPENAI_API_KEY: str = ""
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "https://postpilot.vercel.app"]

    # AI Text Provider
    AI_TEXT_PROVIDER: str = "openai"    # "openai" | "gemini"
    AI_TEXT_MODEL: str = "gpt-4o"       # gpt-4o | gemini-1.5-pro
    AI_MINI_MODEL: str = "gpt-4o-mini"  # gpt-4o-mini | gemini-1.5-flash

    # AI Image Provider
    AI_IMAGE_PROVIDER: str = "openai"   # "openai" | "gemini"
    AI_IMAGE_MODEL: str = "dall-e-3"    # dall-e-3 | imagen-3.0-generate-001
    AI_IMAGE_SIZE: str = "1024x1024"

    # Gemini API Key
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
