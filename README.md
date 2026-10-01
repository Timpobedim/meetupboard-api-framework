# MeetupBoard API Framework — проектный фреймворк API-автотестов

Фреймворк API-тестов для MeetupBoard — афиши IT-митапов из раздела Python Backend этого
портфолио. Клиент сгенерирован из OpenAPI, каждый ответ проверяется Pydantic-схемой, тестовые данные
строит Builder на Faker, а то, что данные действительно записаны, проверяется запросами в PostgreSQL
на PyPika. Тесты независимы и идут в 4 потока, результаты собираются для Allure, стенд поднимается
через docker compose, пайплайн — GitLab CI.

**Стек:** Python 3.12 · pytest · pytest-xdist · openapi-generator 7.25 (python, urllib3) · Pydantic v2 ·
Faker · PyPika · psycopg 3 · assertpy · allure-pytest · Docker · GitLab CI · ruff · mypy (strict).

## Решения, которые пришлось принять

1. **Нормализация спецификации перед генерацией** (`framework/spec.py`). Django Ninja даёт
   operationId вида `apps_events_api_create_event` и русские теги роутеров — генератор сделал бы из них
   нечитаемые методы и классы. Перед генерацией остаются только `/api`, короткие operationId
   (`create_event`, `attend`), латинские теги и используемые схемы; служебные эндпоинты jwtninja убраны.
2. **Тест дрейфа контракта.** Живая спецификация стенда проходит ту же нормализацию и сравнивается
   с `openapi/meetupboard.json`, по которой сгенерирован клиент. Новая операция без operationId в
   таблице — `UnknownOperationError`, изменённая — падение с подсказкой `make codegen`.
3. **Ответы в спецификации описаны как `Any`**, поэтому сгенерированные методы возвращают `object`.
   Контракт ответов держат Pydantic-схемы фреймворка — ровно та причина, по которой статья ставит
   слой Pydantic поверх клиента.
4. **Генератор не справился со схемой частичного обновления профиля:** служебный маркер «поле не
   передано» превратился в anyOf-обёртки (`Bio`, `Email`, …). Этот запрос идёт через свой клиент —
   тот самый «нестандартный сценарий» из статьи.
5. **Гонка за последнее место.** Шесть одновременных заявок на мероприятие с одним местом: ровно
   одна получает 200, пять — 409, в таблице участников одна строка. Так проверяется, что сервис
   блокирует строку (`SELECT … FOR UPDATE`) на PostgreSQL.

## Тестируемый сервис

MeetupBoard собирается из соседней папки `03-python-backend/meetups-django-ninja`, стенд слушает
порты 8003 (API) и 5433 (PostgreSQL для проверок). В отдельном репозитории вместо сборки
подставляется образ из registry — переменная `AUT_IMAGE` в `.gitlab-ci.yml`.

## Запуск

```bash
make up            # MeetupBoard + PostgreSQL в Docker
uv sync --group dev
make test          # 4 потока, результаты — в allure-results
make test-docker   # то же в контейнере, как в CI
make report        # отчёт Allure (нужен Allure CLI)
make lint          # ruff + mypy
make spec codegen  # если API изменилось: обновить спецификацию и пересоздать клиент
```

## Структура

```
framework/
├── clients/        # generated.py — фабрика сгенерированного клиента, raw.py — клиент на requests
├── models/         # Pydantic-схемы ответов
├── builders/       # Builder'ы тел запросов на Faker
├── db/             # таблицы и запросы PyPika, чтение из PostgreSQL
├── steps.py        # бизнес-шаги Allure: регистрация, мероприятие, комментарий
├── spec.py         # нормализация OpenAPI для кодогенерации и теста дрейфа
└── config.py       # адреса стенда из переменных окружения MEETUPBOARD_*
clients/meetupboard_client/   # сгенерированный клиент — руками не правится
openapi/meetupboard.json      # спецификация, по которой он сгенерирован
scripts/            # prepare_spec.py, codegen.sh
tests/              # contract, accounts, events, comments, negative
```

## Результат прогона

27 тестов проходят примерно за 9 секунд в 4 потока — и с машины разработчика, и внутри контейнера
(`make test-docker`, образ собирается из `uv.lock`); ruff и mypy (strict) — без замечаний.
Проверено 11.09.2026 на стенде из `docker-compose.yml` (PostgreSQL 16, MeetupBoard на gunicorn).
Пайплайн GitLab CI написан, но не запускался: у портфолио нет удалённого репозитория.
