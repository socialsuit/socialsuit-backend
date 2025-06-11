from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # PostgreSQL
    DATABASE_URL: str

    # MongoDB
    MONGODB_URL: str

    # Redis
    REDIS_URL: str

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # JWT Secret
    JWT_SECRET: str

    # Optional: Environment Mode
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        extra = "allow"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()