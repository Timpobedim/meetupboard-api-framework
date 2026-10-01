from __future__ import annotations

from typing import Self

from faker import Faker
from meetupboard_client.models import CommentContainerSchemaIn, CommentInSchema

_fake = Faker("ru_RU")


class CommentBuilder:
    def __init__(self) -> None:
        self.body = _fake.sentence(nb_words=10)

    def with_body(self, body: str) -> Self:
        self.body = body
        return self

    def build(self) -> CommentContainerSchemaIn:
        return CommentContainerSchemaIn(comment=CommentInSchema(body=self.body))
