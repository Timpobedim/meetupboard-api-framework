"""Авторизация: без токена, с испорченным токеном, оба префикса схемы, исключения сгенерированного клиента."""

from __future__ import annotations

import allure
import pytest
from assertpy import assert_that
from meetupboard_client.exceptions import NotFoundException, UnauthorizedException

from framework.builders import EventBuilder
from framework.clients.generated import build_api
from framework.clients.raw import RawClient
from framework.config import Settings
from framework.models.responses import ErrorBody, UserEnvelope
from framework.steps import Member

pytestmark = allure.feature("Авторизация")


def test_request_without_token_is_rejected(anonymous: RawClient) -> None:
    response = anonymous.post("/api/events", EventBuilder().build_dict())

    assert_that(response.status_code).is_equal_to(401)
    assert_that(ErrorBody.model_validate(response.json()).errors).is_equal_to({"token": ["отсутствует"]})


def test_broken_token_is_rejected(settings: Settings) -> None:
    response = RawClient(settings, token="broken.token.value").get("/api/user")

    assert_that(response.status_code).is_equal_to(401)
    assert_that(ErrorBody.model_validate(response.json()).errors).is_equal_to({"token": ["invalid_token"]})


@pytest.mark.parametrize("prefix", ["Token", "Bearer"])
def test_both_token_prefixes_are_accepted(settings: Settings, organizer: Member, prefix: str) -> None:
    response = RawClient(settings, token=organizer.token, prefix=prefix).get("/api/user")

    assert_that(response.status_code).is_equal_to(200)
    assert_that(UserEnvelope.model_validate(response.json()).user.username).is_equal_to(organizer.username)


def test_generated_client_raises_typed_exceptions(settings: Settings) -> None:
    with pytest.raises(NotFoundException):
        build_api(settings).events.get_event("no-such-event")
    with pytest.raises(UnauthorizedException):
        build_api(settings).accounts.get_current_user()
