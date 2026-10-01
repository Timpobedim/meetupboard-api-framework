"""Свой клиент на requests — для нестандартных сценариев.

Сгенерированный клиент сам валидирует тела запросов и бросает исключения на 4xx: заведомо
неверный запрос через него не отправить, а в негативных тестах проверяется именно ответ сервера.
Кроме того, генератор не справился со схемой частичного обновления профиля (anyOf со служебным
маркером EMPTY) — PUT /api/user тоже идёт через этот клиент.
"""

from __future__ import annotations

import json
from typing import Any

import allure
import requests

from framework.config import Settings


class RawClient:
    def __init__(self, settings: Settings, token: str | None = None, prefix: str = "Token") -> None:
        self._base_url = settings.api_url.rstrip("/")
        self._timeout = settings.timeout
        self._session = requests.Session()
        if token is not None:
            self._session.headers["Authorization"] = f"{prefix} {token}"

    def request(
        self, method: str, path: str, *, json_body: Any = None, params: dict[str, Any] | None = None
    ) -> requests.Response:
        with allure.step(f"HTTP {method} {path}"):
            response = self._session.request(
                method, f"{self._base_url}{path}", json=json_body, params=params, timeout=self._timeout
            )
            body = json.dumps(json_body, ensure_ascii=False, indent=2) if json_body is not None else ""
            allure.attach(f"{method} {response.url}\n\n{body}", "запрос", allure.attachment_type.TEXT)
            allure.attach(f"{response.status_code}\n\n{response.text}", "ответ", allure.attachment_type.TEXT)
        return response

    def get(self, path: str, params: dict[str, Any] | None = None) -> requests.Response:
        return self.request("GET", path, params=params)

    def post(self, path: str, json_body: Any = None) -> requests.Response:
        return self.request("POST", path, json_body=json_body)

    def put(self, path: str, json_body: Any) -> requests.Response:
        return self.request("PUT", path, json_body=json_body)

    def delete(self, path: str) -> requests.Response:
        return self.request("DELETE", path)
