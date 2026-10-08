# SaverAI

Savings assistant for bank customers (BME, AI Assisted Software Development homework).
Everything banking-related is simulated. The app contains no AI service; see `docs/ai-usage.md`
for how AI tools were used during development.

## Requirements
- Python 3.12 and [uv](https://docs.astral.sh/uv/)

## Setup and run
    make setup      # install backend deps, create .env from .env.example
    make migrate    # create the SQLite database
    make dev        # backend on http://localhost:8000 (admin: /admin/, API docs: /api/docs)

## Run with Docker
    make setup                  # only to create .env (or: cp .env.example .env)
    docker compose up --build   # backend on http://localhost:8000, applies migrations on start

## Quality
    make test       # pytest
    make lint       # ruff + mypy
    make fmt        # auto-fix lint and formatting
    make check      # run before every commit

Specification: `docs/specification.md`. Agent instructions: `AGENTS.md`.
