from __future__ import annotations

import uuid
from typing import Self

from faker import Faker
from meetupboard_client.models import UserCreateSchema, UserInCreateSchema

_fake = Faker("ru_RU")

DEFAULT_PASSWORD = "Secret-pass-123"


class UserBuilder:
    """Тело регистрации. Логин и email уникальны — тесты не мешают друг другу в параллельном прогоне."""

    def __init__(self) -> None:
        self.username = f"{_fake.user_name()}_{uuid.uuid4().hex[:8]}"
        self.email = f"{self.username}@example.com"
        self.password = DEFAULT_PASSWORD

    def with_username(self, username: str) -> Self:
        self.username = username
        return self

    def with_email(self, email: str) -> Self:
        self.email = email
        return self

    def with_password(self, password: str) -> Self:
        self.password = password
        return self

    def build(self) -> UserCreateSchema:
        return UserCreateSchema(
            user=UserInCreateSchema(email=self.email, username=self.username, password=self.password)
        )
