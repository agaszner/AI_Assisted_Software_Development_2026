# SaverAI commands (AGENTS.md section 4).
-include .env
export

.PHONY: setup migrate seed dev dev-backend dev-frontend test test-fe e2e lint fmt docs-check check

setup:
	test -f .env || cp .env.example .env
	cd backend && uv sync
	cd frontend && npm ci && npx playwright install chromium

migrate:
	cd backend && uv run python manage.py migrate

seed: migrate
	cd backend && uv run python manage.py seed

dev:
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	cd backend && uv run python manage.py runserver 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && uv run pytest

test-fe:
	cd frontend && npm test

# Starts both servers if they are not running. Resets the local database (flush, migrate, seed).
e2e:
	cd frontend && npx playwright test

lint:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy .
	cd frontend && npm run lint

fmt:
	cd backend && uv run ruff check --fix . && uv run ruff format .
	cd frontend && npm run fmt

docs-check:
	python3 scripts/docs_check.py

check: lint test test-fe docs-check
