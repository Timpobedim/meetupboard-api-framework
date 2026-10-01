.PHONY: up down spec codegen test test-docker lint report

up:            ## поднять стенд: MeetupBoard + PostgreSQL
	docker compose up -d --build --wait db aut

down:          ## остановить стенд и удалить данные
	docker compose down -v

spec:          ## обновить openapi/meetupboard.json с запущенного стенда
	uv run python -m scripts.prepare_spec

codegen:       ## пересоздать клиент по openapi/meetupboard.json
	./scripts/codegen.sh

test:          ## тесты с машины разработчика (стенд должен быть поднят)
	uv run pytest

test-docker:   ## тесты в контейнере — так же, как в CI
	docker compose --profile tests run --rm tests

lint:          ## линтер, форматирование и типы
	uv run ruff check . && uv run ruff format --check . && uv run mypy

report:        ## открыть отчёт Allure (нужен allure CLI)
	allure serve allure-results
