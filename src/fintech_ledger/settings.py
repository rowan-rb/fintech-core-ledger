from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://fintech:fintech@localhost:5433/fintech"
    )
    RABBITMQ_URL: str = Field(
        default="amqp://fintech:fintech@localhost:5672/"
    )
    # Fallback if .env file is missing (for CI)
    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def rabbitmq_url(self) -> str:
        return self.RABBITMQ_URL

settings = Settings()