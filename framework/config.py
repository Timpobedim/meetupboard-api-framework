from __future__ import annotations

from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Адреса стенда из переменных окружения MEETUPBOARD_*.

    По умолчанию — стенд из docker-compose.yml этого проекта: API на 8003, PostgreSQL на 5433
    (порты сдвинуты, чтобы не мешать самому MeetupBoard, запущенному из его папки).
    """

    model_config = SettingsConfigDict(env_prefix="MEETUPBOARD_")

    api_url: str = "http://localhost:8003"
    db_dsn: str = "postgresql://postgres:postgres@localhost:5433/meetups"
    timeout: float = 15.0


@cache
def get_settings() -> Settings:
    return Settings()
