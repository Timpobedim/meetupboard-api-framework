from __future__ import annotations

from typing import Any

import allure
import psycopg
from psycopg.rows import dict_row
from pypika.queries import QueryBuilder


class Database:
    """Только чтение: тесты проверяют, что API действительно записало данные, но сами в БД не пишут."""

    def __init__(self, dsn: str) -> None:
        self._connection = psycopg.connect(dsn, autocommit=True, row_factory=dict_row)

    def close(self) -> None:
        self._connection.close()

    def fetch_all(self, query: QueryBuilder, *params: Any) -> list[dict[str, Any]]:
        sql = query.get_sql()
        with allure.step("SQL-проверка"):
            with self._connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
            allure.attach(
                f"{sql}\n\nпараметры: {params}\n\nстрок: {len(rows)}", "запрос", allure.attachment_type.TEXT
            )
        return rows

    def fetch_one(self, query: QueryBuilder, *params: Any) -> dict[str, Any] | None:
        rows = self.fetch_all(query, *params)
        return rows[0] if rows else None

    def fetch_column(self, query: QueryBuilder, *params: Any) -> list[Any]:
        return [next(iter(row.values())) for row in self.fetch_all(query, *params)]
