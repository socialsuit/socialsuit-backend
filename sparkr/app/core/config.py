import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    # API configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Sparkr API"
    DESCRIPTION: str = "API for Sparkr social media campaign management"
    VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development_secret_key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    # Database
    DB_URL: str = os.getenv("DB_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/sparkr")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # External APIs
    TWITTER_BEARER: str = os.getenv("TWITTER_BEARER", "")
    IG_APP_ID: str = os.getenv("IG_APP_ID", "")
    IG_APP_SECRET: str = os.getenv("IG_APP_SECRET", "")
    
    class Config:
        case_sensitive = True


settings = Settings()