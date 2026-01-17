FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_HTTP_TIMEOUT=3000

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        unzip \
        dpkg \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

RUN uv lock && uv sync --no-dev --locked

COPY . /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

CMD uv run main.py