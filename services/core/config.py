from pydantic import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET: str = "supersecurekey"
    DATABASE_URL: str = "postgresql://username:password@localhost/db"

    class Config:
        env_file = ".env"

settings = Settings()
