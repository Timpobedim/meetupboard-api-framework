"""Запросы для проверок в БД на PyPika.

Значения не подставляются в строку SQL: вместо них Parameter("%s"), а сами значения уходят
в psycopg отдельно — это и защита от инъекций, и SQL, который читается как SQL.
"""

from __future__ import annotations

from pypika import Parameter, PostgreSQLQuery
from pypika.queries import QueryBuilder

from framework.db.tables import attendees, comments, event_tags, events, followers, tags, users

VALUE = Parameter("%s")


def user_by_username() -> QueryBuilder:
    return (
        PostgreSQLQuery.from_(users)
        .select(users.id, users.email, users.username, users.bio, users.image)
        .where(users.username == VALUE)
    )


def event_by_slug() -> QueryBuilder:
    return (
        PostgreSQLQuery.from_(events)
        .select(
            events.id,
            events.slug,
            events.title,
            events.capacity,
            events.city,
            events.is_online,
            events.starts_at,
            events.organizer_id,
        )
        .where(events.slug == VALUE)
    )


def tag_names_of_event() -> QueryBuilder:
    return (
        PostgreSQLQuery.from_(event_tags)
        .join(tags)
        .on(event_tags.tag_id == tags.id)
        .select(tags.name)
        .where(event_tags.event_id == VALUE)
        .orderby(tags.name)
    )


def attendee_usernames() -> QueryBuilder:
    return (
        PostgreSQLQuery.from_(attendees)
        .join(users)
        .on(attendees.user_id == users.id)
        .select(users.username)
        .where(attendees.event_id == VALUE)
        .orderby(users.username)
    )


def comments_of_event() -> QueryBuilder:
    return (
        PostgreSQLQuery.from_(comments)
        .join(users)
        .on(comments.author_id == users.id)
        .select(comments.id, comments.content, users.username)
        .where(comments.event_id == VALUE)
        .orderby(comments.id)
    )


def follower_usernames() -> QueryBuilder:
    """Подписчики пользователя с логином-параметром."""
    followed = users.as_("followed")
    follower = users.as_("follower")
    return (
        PostgreSQLQuery.from_(followers)
        .join(followed)
        .on(followers.from_user_id == followed.id)
        .join(follower)
        .on(followers.to_user_id == follower.id)
        .select(follower.username)
        .where(followed.username == VALUE)
        .orderby(follower.username)
    )
