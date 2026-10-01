"""Дрейф контракта: клиент сгенерирован по openapi/meetupboard.json — он должен совпадать с живым API."""

from __future__ import annotations

import json
from pathlib import Path

import allure
from assertpy import assert_that

from framework.clients.raw import RawClient
from framework.spec import normalize

pytestmark = allure.feature("Контракт API")

COMMITTED_SPEC = Path(__file__).resolve().parents[2] / "openapi" / "meetupboard.json"


def test_live_spec_matches_committed_spec(anonymous: RawClient) -> None:
    live = normalize(anonymous.get("/openapi.json").json())
    committed = json.loads(COMMITTED_SPEC.read_text(encoding="utf-8"))

    changed = sorted(
        path
        for path in set(live["paths"]) | set(committed["paths"])
        if live["paths"].get(path) != committed["paths"].get(path)
    )
    assert_that(changed).described_as("операции изменились — перегенерируйте клиент: make codegen").is_empty()
    assert_that(live["components"]).is_equal_to(committed["components"])
