"""Подготовка спецификации MeetupBoard к кодогенерации.

Django Ninja генерирует operationId вида apps_events_api_create_event и русские теги роутеров,
а генератор клиента делает из тегов имена классов, из operationId — имена методов. Поэтому
спецификация нормализуется: только /api (служебные эндпоинты jwtninja не нужны), короткие
operationId, латинские теги и только используемые схемы.

Та же функция используется в тесте дрейфа контракта: живая спецификация стенда после нормализации
должна совпадать с закоммиченной openapi/meetupboard.json, по которой сгенерирован клиент.
"""

from __future__ import annotations

import copy
import json
from typing import Any

OPERATION_IDS: dict[tuple[str, str], str] = {
    ("post", "/api/users"): "register",
    ("post", "/api/users/login"): "login",
    ("get", "/api/user"): "get_current_user",
    ("put", "/api/user"): "update_current_user",
    ("get", "/api/profiles/{username}"): "get_profile",
    ("post", "/api/profiles/{username}/follow"): "follow",
    ("delete", "/api/profiles/{username}/follow"): "unfollow",
    ("get", "/api/events"): "list_events",
    ("post", "/api/events"): "create_event",
    ("get", "/api/events/feed"): "feed",
    ("get", "/api/events/{slug}"): "get_event",
    ("put", "/api/events/{slug}"): "update_event",
    ("delete", "/api/events/{slug}"): "delete_event",
    ("post", "/api/events/{slug}/attend"): "attend",
    ("delete", "/api/events/{slug}/attend"): "unattend",
    ("get", "/api/tags"): "list_tags",
    ("get", "/api/events/{slug}/comments"): "list_comments",
    ("post", "/api/events/{slug}/comments"): "add_comment",
    ("delete", "/api/events/{slug}/comments/{comment_id}"): "delete_comment",
}

TAGS = {
    "accounts": "Пользователи и профили",
    "events": "Мероприятия и запись на них",
    "comments": "Обсуждения мероприятий",
}


class UnknownOperationError(KeyError):
    """В API появилась операция, которой нет в OPERATION_IDS: контракт изменился."""


def _tag_for(path: str) -> str:
    if "/comments" in path:
        return "comments"
    if path.startswith(("/api/events", "/api/tags")):
        return "events"
    return "accounts"


def _refs(node: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                found.add(value.rsplit("/", 1)[-1])
            else:
                found |= _refs(value)
    elif isinstance(node, list):
        for item in node:
            found |= _refs(item)
    return found


def normalize(spec: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(spec)

    paths: dict[str, Any] = {}
    for path, operations in result["paths"].items():
        if not path.startswith("/api/"):
            continue
        for method, operation in operations.items():
            key = (method, path)
            if key not in OPERATION_IDS:
                raise UnknownOperationError(f"{method.upper()} {path}: добавьте operationId в OPERATION_IDS")
            operation["operationId"] = OPERATION_IDS[key]
            operation["tags"] = [_tag_for(path)]
        paths[path] = operations
    result["paths"] = paths

    # Оставляем только схемы, на которые ссылаются операции, — с учётом вложенных ссылок.
    schemas: dict[str, Any] = result.get("components", {}).get("schemas", {})
    used = _refs(paths)
    frontier = set(used)
    while frontier:
        nested = set().union(*(_refs(schemas[name]) for name in frontier if name in schemas)) - used
        used |= nested
        frontier = nested
    result.setdefault("components", {})["schemas"] = {
        name: schemas[name] for name in sorted(used) if name in schemas
    }
    result["tags"] = [{"name": name, "description": description} for name, description in TAGS.items()]
    return result


def dumps(spec: dict[str, Any]) -> str:
    return json.dumps(spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
