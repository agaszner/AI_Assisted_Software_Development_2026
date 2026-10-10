# SaverAI commands (AGENTS.md section 4). Frontend targets are added by the frontend plan.
-include .env
export

.PHONY: setup migrate seed dev test lint fmt docs-check check

setup:
	test -f .env || cp .env.example .env
	cd backend && uv sync

migrate:
	cd backend && uv run python manage.py migrate

seed: migrate
	cd backend && uv run python manage.py seed

dev:
	cd backend && uv run python manage.py runserver 8000

test:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy .

fmt:
	cd backend && uv run ruff check --fix . && uv run ruff format .

docs-check:
	python3 scripts/docs_check.py

check: lint test docs-check
