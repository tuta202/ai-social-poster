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

    class Config:
        env_file = ".env"


settings = Settings()
