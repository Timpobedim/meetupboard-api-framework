# Образ с автотестами: одинаковое окружение на машине разработчика и в CI.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY clients ./clients
RUN uv sync --frozen --no-dev

COPY framework ./framework
COPY scripts ./scripts
COPY openapi ./openapi
COPY tests ./tests

CMD ["pytest"]
