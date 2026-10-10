FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.10.2 /uv /usr/local/bin/uv

# Keep the virtualenv outside /app so the bind mount in docker-compose.yml does not hide it.
ENV UV_PROJECT_ENVIRONMENT=/venv PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
COPY . .

EXPOSE 8000
CMD ["sh", "-c", "uv run python manage.py migrate && uv run python manage.py runserver 0.0.0.0:8000"]
