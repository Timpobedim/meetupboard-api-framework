"""Запись на мероприятия: места, повторная запись, отмена и гонка за последнее место."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import allure
import requests
from assertpy import assert_that

from framework.builders import EventBuilder
from framework.config import Settings
from framework.db import queries
from framework.db.database import Database
from framework.models.responses import ErrorBody, Event, EventEnvelope
from framework.steps import Member, create_event, register_member

pytestmark = allure.feature("Запись на мероприятия")

CONTENDERS = 6


def event_id(db: Database, slug: str) -> int:
    row = db.fetch_one(queries.event_by_slug(), slug)
    assert row is not None, f"мероприятия {slug} нет в БД"
    return int(row["id"])


def test_attend_and_leave_are_persisted(participant: Member, event: Event, db: Database) -> None:
    joined = EventEnvelope.model_validate(participant.api.events.attend_with_http_info(event.slug).data).event

    assert_that(joined.attending).is_true()
    assert_that(joined.seats_left).is_equal_to((event.capacity or 0) - 1)
    assert_that(db.fetch_column(queries.attendee_usernames(), event_id(db, event.slug))).is_equal_to(
        [participant.username]
    )

    participant.api.events.unattend(event.slug)

    assert_that(db.fetch_column(queries.attendee_usernames(), event_id(db, event.slug))).is_empty()


def test_attending_twice_is_a_conflict(participant: Member, event: Event) -> None:
    participant.api.events.attend(event.slug)

    response = participant.raw.post(f"/api/events/{event.slug}/attend")

    assert_that(response.status_code).is_equal_to(409)
    assert_that(ErrorBody.model_validate(response.json()).errors).is_equal_to(
        {"event": ["вы уже зарегистрированы"]}
    )


def test_full_event_rejects_new_attendee(settings: Settings, organizer: Member, participant: Member) -> None:
    event = create_event(organizer, EventBuilder().with_capacity(1))
    participant.api.events.attend(event.slug)
    latecomer = register_member(settings)

    response = latecomer.raw.post(f"/api/events/{event.slug}/attend")

    assert_that(response.status_code).is_equal_to(409)
    assert_that(ErrorBody.model_validate(response.json()).errors).is_equal_to(
        {"event": ["свободных мест нет"]}
    )


def test_last_seat_goes_to_exactly_one_of_concurrent_requests(
    settings: Settings, organizer: Member, db: Database
) -> None:
    """Сервис блокирует строку мероприятия (SELECT … FOR UPDATE): из одновременных заявок
    на последнее место проходит ровно одна, остальные получают 409."""
    event = create_event(organizer, EventBuilder().with_capacity(1))
    contenders = [register_member(settings) for _ in range(CONTENDERS)]

    def attend(member: Member) -> int:
        # Прямой requests: сессии клиентов и шаги Allure не рассчитаны на потоки.
        response = requests.post(
            f"{settings.api_url}/api/events/{event.slug}/attend",
            headers={"Authorization": f"Token {member.token}"},
            timeout=settings.timeout,
        )
        return response.status_code

    with ThreadPoolExecutor(max_workers=CONTENDERS) as pool:
        statuses = list(pool.map(attend, contenders))

    assert_that(sorted(statuses)).is_equal_to([200] + [409] * (CONTENDERS - 1))
    assert_that(db.fetch_column(queries.attendee_usernames(), event_id(db, event.slug))).is_length(1)
