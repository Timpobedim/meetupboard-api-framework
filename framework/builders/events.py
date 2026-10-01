from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any, Self

from faker import Faker
from meetupboard_client.models import EventCreateSchema, EventInCreateSchema

_fake = Faker("ru_RU")

TOPICS = ("Python-митап", "Вечер SQL", "DevOps-завтрак", "Митап по тестированию", "Data-встреча")


class EventBuilder:
    """Тело создания мероприятия: по умолчанию — очная встреча через неделю-две, 50 мест."""

    def __init__(self) -> None:
        self.title = f"{_fake.random_element(TOPICS)} №{_fake.random_int(1, 999)}"
        self.description = _fake.sentence(nb_words=8)
        self.body = _fake.paragraph(nb_sentences=3)
        self.starts_at = datetime.now(UTC) + timedelta(
            days=_fake.random_int(7, 14), hours=_fake.random_int(0, 23)
        )
        self.city = _fake.city_name()
        self.venue = f"Коворкинг «{_fake.word().capitalize()}»"
        self.is_online = False
        self.capacity: int | None = 50
        self.tags = ["python", "митап"]

    def with_title(self, title: str) -> Self:
        self.title = title
        return self

    def with_capacity(self, capacity: int | None) -> Self:
        self.capacity = capacity
        return self

    def with_tags(self, tags: list[str]) -> Self:
        self.tags = tags
        return self

    def online(self) -> Self:
        self.is_online = True
        self.city = ""
        self.venue = ""
        return self

    def starting_in(self, delta: timedelta) -> Self:
        self.starts_at = datetime.now(UTC) + delta
        return self

    def build(self) -> EventCreateSchema:
        return EventCreateSchema(
            event=EventInCreateSchema(
                title=self.title,
                description=self.description,
                body=self.body,
                starts_at=self.starts_at,
                city=self.city,
                is_online=self.is_online,
                venue=self.venue,
                capacity=self.capacity,
                tag_list=self.tags,
            )
        )

    def build_dict(self) -> dict[str, Any]:
        """Тело как JSON-словарь — чтобы испортить одно поле в негативном тесте."""
        payload: dict[str, Any] = json.loads(self.build().to_json())
        return payload
