# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Django 5 + Django Ninja backend skeleton with session login, `customer` / `admin` roles and a Makefile (ADR-0001).
- `make docs-check`: AC ↔ traceability, referenced tests exist, changelog touched (AGENTS.md 8.6).
- ADR-0002 records rule interpretations for spec-silent edge cases and the M2 scope.
- Injected `Clock` (`core/clock.py`), integer-forint money helpers, calendar-month helpers and default rule parameters (`rules/defaults.py`).
- Purity test: `rules/` may not import Django or read the system clock (golden rule 4).
- Monthly surplus analysis: median of the last 6 complete months, 70 % suggested amount, no amount without surplus (AC1, AC5, ADR-0002).
- Deterministic synthetic transaction generator (`banking/synthetic.py`).
- Confidence level: no estimate under 3 months, low confidence for 3–5 months (AC6).
- `docker-compose.yml` and backend `Dockerfile`: `docker compose up --build` runs the backend with migrations applied.
- Plan allocation: emergency fund → planned expenses → investment; ≤ 12-month money only in liquid low-risk products; no product above the customer's risk score (AC2, AC3, ADR-0002).
- Plan proposal outcomes: plan, no surplus (AC5), expected savings needed (AC6).
- Financial time machine: replays the plan on the last 12 complete months and flags skipped months below the 100,000 HUF minimum; Hypothesis property test (AC4, ADR-0002).
- Mandate check `check_action()` with numbered clauses (§1 products and monthly maximum, §2 minimum balance, §3 per-transfer approval, §4 pause); Hypothesis property test.
- Data model: accounts, transactions, products, rule configuration, questionnaire, plans, mandates, recurring orders, executions, audit log (see `docs/architecture.md`).
- Django admin for the product catalogue and rule parameters (Admin role).
- `make seed`: product catalogue, admin user and personas for AC1, AC2, AC5 and AC6.
- Fixed explanation templates filled from rule results (`plans/explanations.py`).
- Monthly order execution through the mandate check with an idempotency key per order and executed month (AC7); low-confidence transfers wait for customer approval (AC6); log stores mandate version and clause. `manage.py run_orders [--period YYYY-MM]`; no future month, no month before the mandate was signed (ADR-0002, AI usage Cases 2 and 4).
- Manual checks (`docs/manual-checks.md`), AI usage working-method section and Case 4 draft.
- Customer API: questionnaire, spending analysis, plan proposal and review, time machine, accept / reject / edit / pause, active plan, transfer approval. Strict integer money validation and past-date check return 422; another customer's plan returns 403; state conflicts return 409; CSRF enforced on session POSTs (AC5, AC6, AC8).
- Plan services: questionnaire with past-date check (AC8), proposal (AC5, AC6), acceptance with versioned mandate and exactly-once recurring orders, rejection (AC7), amount edit, pause, ownership check (AC8).
- React + TypeScript + Vite frontend skeleton with Vitest, ESLint, Prettier; `make dev` runs backend and frontend, new `make test-fe` and `make e2e` (ADR-0003).
- `make docs-check` also verifies frontend test references in `docs/traceability.md`.

### Changed
- Frontend target is a responsive web UI instead of a mobile UI: left sidebar, focused plan flow, sticky summary panel, password-confirmation modal, execution log table; new Figma file (AI usage case 3).
