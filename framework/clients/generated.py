"""Сгенерированный клиент (openapi-generator, транспорт urllib3) — основной способ ходить в API.

Методы клиента возвращают `object`: в спецификации MeetupBoard ответы описаны как Any. Поэтому
каждый ответ проходит через Pydantic-схему из framework.models — см. framework.steps.
"""

from __future__ import annotations

from dataclasses import dataclass

from meetupboard_client import ApiClient, Configuration
from meetupboard_client.api import AccountsApi, CommentsApi, EventsApi

from framework.config import Settings


@dataclass(frozen=True)
class MeetupBoardApi:
    accounts: AccountsApi
    events: EventsApi
    comments: CommentsApi


def build_api(settings: Settings, token: str | None = None) -> MeetupBoardApi:
    """Клиент от имени пользователя с токеном (или анонимный). Схема авторизации — Bearer."""
    client = ApiClient(Configuration(host=settings.api_url, access_token=token))
    return MeetupBoardApi(accounts=AccountsApi(client), events=EventsApi(client), comments=CommentsApi(client))
