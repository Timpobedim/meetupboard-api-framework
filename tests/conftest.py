"""Фикстуры: стенд, БД для проверок, свежие участники и мероприятие на каждый тест."""

from __future__ import annotations

import time
from collections.abc import Iterator

import pytest
import requests

from framework.clients.raw import RawClient
from framework.config import Settings, get_settings
from framework.db.database import Database
from framework.models.responses import Event
from framework.steps import Member, create_event, register_member

STAND_STARTUP_SECONDS = 120


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session", autouse=True)
def _stand_is_up(settings: Settings) -> None:
    """После docker compose up сервису нужно время на миграции — ждём, а не роняем первые тесты."""
    deadline = time.monotonic() + STAND_STARTUP_SECONDS
    while True:
        try:
            if requests.get(f"{settings.api_url}/api/tags", timeout=5).ok:
                return
        except requests.RequestException:
            pass
        if time.monotonic() > deadline:
            pytest.exit(f"MeetupBoard не отвечает: {settings.api_url}", returncode=3)
        time.sleep(2)


@pytest.fixture(scope="session")
def db(settings: Settings) -> Iterator[Database]:
    database = Database(settings.db_dsn)
    yield database
    database.close()


@pytest.fixture
def organizer(settings: Settings) -> Member:
    return register_member(settings)


@pytest.fixture
def participant(settings: Settings) -> Member:
    return register_member(settings)


@pytest.fixture
def event(organizer: Member) -> Event:
    return create_event(organizer)


@pytest.fixture
def anonymous(settings: Settings) -> RawClient:
    return RawClient(settings)
