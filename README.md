# SaverAI

Savings assistant for bank customers (BME, AI Assisted Software Development homework).
Everything banking-related is simulated. The app contains no AI service; see `docs/ai-usage.md`
for how AI tools were used during development.

## Requirements
- Python 3.12 and [uv](https://docs.astral.sh/uv/)

## Setup and run
    make setup      # install backend deps, create .env from .env.example
    make migrate    # create the SQLite database
    make seed       # products, admin user and demo personas (password: SEED_PASSWORD in .env)
    make dev        # backend on http://localhost:8000 (admin: /admin/, API docs: /api/docs)
    cd backend && uv run python manage.py run_orders   # execute this month's orders (idempotent)
    cd backend && uv run python manage.py run_orders --period 2026-09   # late run for a past month

## Demo personas (`make seed`)
| User | Data | Shows |
| --- | --- | --- |
| anna | 6 months, surpluses 100k/120k/80k/110k/90k/300k | AC1 (73,500 HUF), AC2 when no emergency fund is entered |
| bence | 6 months, −40k each | AC5 no surplus |
| csilla | 2 months | AC6 asks for expected savings |
| dani | 4 months | AC6 low confidence, per-transfer approval |
| admin | staff user | Django admin: products, rule parameters |

## API
Interactive docs at http://localhost:8000/api/docs after `make dev`. Log in with
`POST /api/auth/login`; customer endpoints: questionnaire, analysis, plans (propose, review,
edit, accept, reject, pause, time machine), executions (list, approve).

## Run with Docker
    make setup                  # only to create .env (or: cp .env.example .env)
    docker compose up --build   # backend on http://localhost:8000, applies migrations on start

## Quality
    make test       # pytest
    make lint       # ruff + mypy
    make fmt        # auto-fix lint and formatting
    make check      # run before every commit

Specification: `docs/specification.md`. Agent instructions: `AGENTS.md`.
