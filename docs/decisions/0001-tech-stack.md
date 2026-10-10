# 0001. Backend tech stack and dependencies
Date: 2026-10-06 · Status: accepted

## Context
SaverAI needs a small, testable backend for a university homework: a pure rule engine, a few
models, an admin UI for products and rule parameters, and a JSON API for a React frontend.
AGENTS.md section 3 fixes the stack; this ADR lists every backend dependency so none is added silently.

## Decision
- Python 3.12, managed with **uv** (`backend/pyproject.toml`, `backend/uv.lock`).
- Runtime: **Django 5.2** (ORM, migrations, auth, admin), **django-ninja 1.x** (API, brings Pydantic 2).
- Dev: **pytest**, **pytest-django**, **hypothesis**, **ruff**, **mypy**, **django-stubs** (mypy plugin).
- SQLite database. Environment variables come from `.env`, loaded by the Makefile (`-include .env`),
  so no python-dotenv.
- No AI / LLM dependency (AGENTS.md golden rule 1).
- Not added in M2: APScheduler (orders run via `manage.py run_orders`, see ADR-0002). Frontend
  dependencies are decided in the frontend plan.

## Alternatives considered
- pip + requirements.txt: no lockfile, slower; uv is already installed on the dev machine.
- Django REST Framework: more boilerplate than Ninja; Ninja gives Pydantic validation (AC8) for free.
- python-dotenv: the Makefile can load `.env` with two lines.

## Consequences
- `make setup` needs uv. Every backend command runs as `uv run ...` inside `backend/`.
- mypy runs in strict mode with the django-stubs plugin; new code must be fully typed.
