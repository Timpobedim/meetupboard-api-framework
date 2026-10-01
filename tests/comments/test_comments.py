"""Обсуждения: комментарий сохраняется, виден в списке, удалить его может автор или организатор."""

from __future__ import annotations

import allure
from assertpy import assert_that

from framework.builders import CommentBuilder
from framework.config import Settings
from framework.db import queries
from framework.db.database import Database
from framework.models.responses import CommentList, Event
from framework.steps import Member, add_comment, register_member

pytestmark = allure.feature("Обсуждения")


def event_id(db: Database, slug: str) -> int:
    row = db.fetch_one(queries.event_by_slug(), slug)
    assert row is not None, f"мероприятия {slug} нет в БД"
    return int(row["id"])


def test_comment_is_stored_and_listed(participant: Member, event: Event, db: Database) -> None:
    comment = add_comment(participant, event.slug, CommentBuilder().with_body("Будет ли запись докладов?"))

    assert_that(comment.author.username).is_equal_to(participant.username)
    rows = db.fetch_all(queries.comments_of_event(), event_id(db, event.slug))
    assert_that(rows).is_length(1)
    assert_that(rows[0]).contains_entry(
        {"content": "Будет ли запись докладов?"}, {"username": participant.username}
    )
    listed = CommentList.model_validate(
        participant.api.comments.list_comments_with_http_info(event.slug).data
    )
    assert_that([item.id for item in listed.comments]).is_equal_to([comment.id])


def test_stranger_can_not_delete_comment(settings: Settings, participant: Member, event: Event) -> None:
    comment = add_comment(participant, event.slug)
    stranger = register_member(settings)

    response = stranger.raw.delete(f"/api/events/{event.slug}/comments/{comment.id}")

    assert_that(response.status_code).is_equal_to(403)


def test_organizer_can_delete_comment(
    organizer: Member, participant: Member, event: Event, db: Database
) -> None:
    comment = add_comment(participant, event.slug)

    response = organizer.raw.delete(f"/api/events/{event.slug}/comments/{comment.id}")

    assert_that(response.status_code).is_equal_to(204)
    assert_that(db.fetch_all(queries.comments_of_event(), event_id(db, event.slug))).is_empty()
