from dataclasses import dataclass
from functools import lru_cache
from os import getenv


@dataclass(frozen=True)
class Settings:
    api_key: str
    database_url: str
    rabbitmq_url: str
    webhook_timeout_seconds: float


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        api_key=getenv("APP_API_KEY", "change-me"),
        database_url=getenv(
            "APP_DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/payments",
        ),
        rabbitmq_url=getenv("APP_RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"),
        webhook_timeout_seconds=float(getenv("APP_WEBHOOK_TIMEOUT_SECONDS", "5")),
    )
