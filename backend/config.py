from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "https://typeracer-webapp.fly.dev"]
    log_level: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()