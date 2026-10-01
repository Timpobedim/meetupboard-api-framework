"""Мероприятия: создание, фильтры, изменение, удаление и валидация — с проверкой записей в БД."""

from __future__ import annotations

import uuid
from typing import Any

import allure
import pytest
from assertpy import assert_that
from meetupboard_client.models import EventInPartialUpdateSchema, EventPartialUpdateSchema

from framework.builders import EventBuilder
from framework.clients.generated import build_api
from framework.config import Settings
from framework.db import queries
from framework.db.database import Database
from framework.models.responses import ErrorBody, Event, EventEnvelope, EventPage
from framework.steps import Member, add_comment, create_event

pytestmark = allure.feature("Мероприятия")


def test_created_event_is_stored(organizer: Member, db: Database) -> None:
    builder = EventBuilder().with_title("Python-митап: асинхронность").with_capacity(80)
    builder.with_tags(["Python", "asyncio", "python"])

    event = create_event(organizer, builder)

    assert_that(event.slug).starts_with("python-mitap-asinkhronnost")
    assert_that(event.tag_list).is_equal_to(["asyncio", "python"])
    assert_that(event.seats_left).is_equal_to(80)
    row = db.fetch_one(queries.event_by_slug(), event.slug)
    author = db.fetch_one(queries.user_by_username(), organizer.username)
    assert row is not None
    assert author is not None
    assert_that(row).contains_entry(
        {"title": "Python-митап: асинхронность"}, {"capacity": 80}, {"organizer_id": author["id"]}
    )
    assert_that(db.fetch_column(queries.tag_names_of_event(), row["id"])).is_equal_to(["asyncio", "python"])


def test_list_filters_by_tag_and_organizer(settings: Settings, organizer: Member) -> None:
    tag = f"tag-{uuid.uuid4().hex[:8]}"
    tagged = create_event(organizer, EventBuilder().with_tags([tag]))
    create_event(organizer, EventBuilder().with_tags(["другое"]))
    api = build_api(settings)

    by_tag = EventPage.model_validate(api.events.list_events_with_http_info(tag=tag).data)
    by_organizer = EventPage.model_validate(
        api.events.list_events_with_http_info(organizer=organizer.username).data
    )

    assert_that([item.slug for item in by_tag.events]).is_equal_to([tagged.slug])
    assert_that(by_organizer.events_count).is_equal_to(2)


def test_organizer_updates_event(organizer: Member, event: Event, db: Database) -> None:
    title = f"Митап по Django {uuid.uuid4().hex[:6]}"
    changes = EventPartialUpdateSchema(event=EventInPartialUpdateSchema(title=title, capacity=120))

    response = organizer.api.events.update_event_with_http_info(event.slug, changes)

    updated = EventEnvelope.model_validate(response.data).event
    assert_that(updated.slug).starts_with("mitap-po-django")
    row = db.fetch_one(queries.event_by_slug(), updated.slug)
    assert_that(row).contains_entry({"title": title}, {"capacity": 120})
    assert_that(db.fetch_one(queries.event_by_slug(), event.slug)).is_none()


def test_stranger_can_not_change_event(participant: Member, event: Event) -> None:
    response = participant.raw.put(f"/api/events/{event.slug}", {"event": {"title": "Чужой митап"}})

    assert_that(response.status_code).is_equal_to(403)
    assert_that(ErrorBody.model_validate(response.json()).errors).is_equal_to({"event": ["нет прав"]})


def test_deleted_event_is_removed_with_comments(
    organizer: Member, participant: Member, event: Event, db: Database
) -> None:
    add_comment(participant, event.slug)
    row = db.fetch_one(queries.event_by_slug(), event.slug)
    assert row is not None

    response = organizer.api.events.delete_event_with_http_info(event.slug)

    assert_that(response.status_code).is_equal_to(204)
    assert_that(db.fetch_one(queries.event_by_slug(), event.slug)).is_none()
    assert_that(db.fetch_all(queries.comments_of_event(), row["id"])).is_empty()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("startsAt", "2020-01-01T10:00:00+03:00", id="past-date"),
        pytest.param("capacity", 0, id="zero-capacity"),
        pytest.param("title", "   ", id="blank-title"),
        pytest.param("tagList", [f"t{index}" for index in range(11)], id="too-many-tags"),
    ],
)
def test_invalid_event_is_rejected(organizer: Member, field: str, value: Any) -> None:
    payload = EventBuilder().build_dict()
    payload["event"][field] = value

    response = organizer.raw.post("/api/events", payload)

    assert_that(response.status_code).is_equal_to(422)
    assert_that(ErrorBody.model_validate(response.json()).errors).contains_key(field)
