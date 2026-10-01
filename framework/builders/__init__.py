"""Builder'ы тел запросов: валидные данные по умолчанию (Faker), тест меняет только то, что проверяет."""

from framework.builders.comments import CommentBuilder
from framework.builders.events import EventBuilder
from framework.builders.users import UserBuilder

__all__ = ["CommentBuilder", "EventBuilder", "UserBuilder"]
