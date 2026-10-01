"""Бизнес-шаги: регистрация участника, создание мероприятия, комментарий.

Каждый шаг идёт через сгенерированный клиент и сразу валидирует ответ Pydantic-схемой — так
контракт ответа проверяется в каждом тесте, а не только в тестах «на схему».
"""

from __future__ import annotations

from dataclasses import dataclass

import allure

from framework.builders import CommentBuilder, EventBuilder, UserBuilder
from framework.clients.generated import MeetupBoardApi, build_api
from framework.clients.raw import RawClient
from framework.config import Settings
from framework.models.responses import Comment, CommentEnvelope, Event, EventEnvelope, UserEnvelope


@dataclass(frozen=True)
class Member:
    """Зарегистрированный пользователь стенда с клиентами от его имени."""

    username: str
    email: str
    password: str
    token: str
    api: MeetupBoardApi
    raw: RawClient


def register_member(settings: Settings, builder: UserBuilder | None = None) -> Member:
    body = (builder or UserBuilder()).build()
    with allure.step(f"Регистрация участника {body.user.username}"):
        response = build_api(settings).accounts.register_with_http_info(
            body, _request_timeout=settings.timeout
        )
        user = UserEnvelope.model_validate(response.data).user
    return Member(
        username=user.username,
        email=user.email,
        password=body.user.password,
        token=user.token,
        api=build_api(settings, user.token),
        raw=RawClient(settings, user.token),
    )


def create_event(member: Member, builder: EventBuilder | None = None) -> Event:
    body = (builder or EventBuilder()).build()
    with allure.step(f"Мероприятие «{body.event.title}» от {member.username}"):
        response = member.api.events.create_event_with_http_info(body)
        return EventEnvelope.model_validate(response.data).event


def add_comment(member: Member, event_slug: str, builder: CommentBuilder | None = None) -> Comment:
    body = (builder or CommentBuilder()).build()
    with allure.step(f"Комментарий {member.username} к {event_slug}"):
        response = member.api.comments.add_comment_with_http_info(event_slug, body)
        return CommentEnvelope.model_validate(response.data).comment
