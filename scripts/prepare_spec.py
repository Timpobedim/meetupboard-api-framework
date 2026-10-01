"""Скачивает спецификацию тестируемого API и готовит её к кодогенерации.

python -m scripts.prepare_spec                                  # с запущенного стенда
python -m scripts.prepare_spec --source path/to/openapi.json    # из файла
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests

from framework.config import get_settings
from framework.spec import dumps, normalize

DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "openapi" / "meetupboard.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--source", help="URL или путь к openapi.json (по умолчанию — стенд из настроек)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    settings = get_settings()
    # NinjaAPI подключён в корень сайта: роутеры живут под /api, а схема — в /openapi.json.
    source: str = args.source or f"{settings.api_url}/openapi.json"
    if source.startswith(("http://", "https://")):
        response = requests.get(source, timeout=settings.timeout)
        response.raise_for_status()
        raw = response.json()
    else:
        raw = json.loads(Path(source).read_text(encoding="utf-8"))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(dumps(normalize(raw)), encoding="utf-8")
    print(f"Спецификация записана: {args.output}")


if __name__ == "__main__":
    main()
