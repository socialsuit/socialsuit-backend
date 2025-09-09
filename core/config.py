from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # PostgreSQL
    DATABASE_URL: str

    # MongoDB
    MONGO_URL: str

    # Redis
    REDIS_URL: str

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # JWT Secret
    JWT_SECRET: str
    
    # OpenRouter API for DeepSeek integration
    OPENROUTER_API_KEY: str
    OPENROUTER_API_URL: str = "https://openrouter.ai/api/v1/chat/completions"
    OPENROUTER_MODEL: str = "deepseek/deepseek-r1-distill-llama-70b"

    # Optional: Environment Mode
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        extra = "allow"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()