"""Pydantic-схемы ответов API.

В OpenAPI MeetupBoard ответы описаны как Any, поэтому контракт ответов фиксируется здесь.
extra="forbid": новое или переименованное поле роняет тест — изменение контракта не пройдёт
незамеченным. Одна схема вместо десятка assert на каждое поле.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)


class Profile(ApiModel):
    username: str
    bio: str | None
    image: str | None
    following: bool


class ProfileEnvelope(ApiModel):
    profile: Profile


class CurrentUser(ApiModel):
    email: str
    username: str
    bio: str | None
    image: str | None
    token: str


class UserEnvelope(ApiModel):
    user: CurrentUser


class EventSummary(ApiModel):
    """Мероприятие в списке — без программы (body)."""

    slug: str
    title: str
    description: str
    starts_at: datetime = Field(alias="startsAt")
    city: str
    is_online: bool = Field(alias="isOnline")
    venue: str
    capacity: int | None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    attending: bool
    attendees_count: int = Field(alias="attendeesCount")
    seats_left: int | None = Field(alias="seatsLeft")
    organizer: Profile
    tag_list: list[str] = Field(alias="tagList")


class Event(EventSummary):
    body: str


class EventEnvelope(ApiModel):
    event: Event


class EventPage(ApiModel):
    events: list[EventSummary]
    events_count: int = Field(alias="eventsCount")


class Comment(ApiModel):
    id: int
    body: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    author: Profile


class CommentEnvelope(ApiModel):
    comment: Comment


class CommentList(ApiModel):
    comments: list[Comment]


class TagList(ApiModel):
    tags: list[str]


class ErrorBody(ApiModel):
    """Единый формат ошибок MeetupBoard: {"errors": {"<поле или ресурс>": ["сообщение"]}}."""

    errors: dict[str, list[str]]
