"""Пользователи: регистрация, вход, профиль, подписки — с проверкой записей в БД."""

from __future__ import annotations

import uuid

import allure
from assertpy import assert_that
from meetupboard_client.models import UserInLoginSchema, UserLoginSchema

from framework.builders import UserBuilder
from framework.clients.generated import build_api
from framework.clients.raw import RawClient
from framework.config import Settings
from framework.db import queries
from framework.db.database import Database
from framework.models.responses import ErrorBody, ProfileEnvelope, UserEnvelope
from framework.steps import Member, register_member

pytestmark = allure.feature("Пользователи")


def test_registration_stores_user_with_lowercased_email(settings: Settings, db: Database) -> None:
    builder = UserBuilder()
    builder.with_email(f"Anna.{uuid.uuid4().hex[:8]}@Example.com")

    member = register_member(settings, builder)

    row = db.fetch_one(queries.user_by_username(), member.username)
    assert_that(row).is_not_none()
    assert row is not None
    assert_that(row["email"]).is_equal_to(builder.email.lower())
    assert_that(member.email).is_equal_to(builder.email.lower())


def test_login_returns_working_token(settings: Settings, organizer: Member) -> None:
    credentials = UserLoginSchema(user=UserInLoginSchema(email=organizer.email, password=organizer.password))

    token = UserEnvelope.model_validate(
        build_api(settings).accounts.login_with_http_info(credentials).data
    ).user.token
    me = UserEnvelope.model_validate(
        build_api(settings, token).accounts.get_current_user_with_http_info().data
    )

    assert_that(me.user.username).is_equal_to(organizer.username)


def test_email_is_unique_regardless_of_case(anonymous: RawClient, organizer: Member) -> None:
    payload = {
        "user": {
            "email": organizer.email.upper(),
            "username": f"x{uuid.uuid4().hex[:10]}",
            "password": "Secret-pass-1",
        }
    }

    response = anonymous.post("/api/users", payload)

    assert_that(response.status_code).is_equal_to(409)
    assert_that(ErrorBody.model_validate(response.json()).errors).is_equal_to({"email": ["уже занято"]})


def test_follow_and_unfollow_are_persisted(participant: Member, organizer: Member, db: Database) -> None:
    followed = participant.api.accounts.follow_with_http_info(organizer.username)

    assert_that(ProfileEnvelope.model_validate(followed.data).profile.following).is_true()
    assert_that(db.fetch_column(queries.follower_usernames(), organizer.username)).is_equal_to(
        [participant.username]
    )

    participant.api.accounts.unfollow(organizer.username)

    assert_that(db.fetch_column(queries.follower_usernames(), organizer.username)).is_empty()


def test_profile_update_is_persisted(organizer: Member, db: Database) -> None:
    changes = {"bio": "Организую митапы по Python", "image": "https://example.com/avatar.png"}

    response = organizer.raw.put("/api/user", {"user": changes})

    assert_that(response.status_code).is_equal_to(200)
    user = UserEnvelope.model_validate(response.json()).user
    assert_that(user.bio).is_equal_to(changes["bio"])
    assert_that(user.token).is_equal_to(organizer.token)
    assert_that(db.fetch_one(queries.user_by_username(), organizer.username)).contains_entry(
        {"bio": changes["bio"]}, {"image": changes["image"]}
    )
