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
- Plan services: questionnaire with past-date check (AC8), proposal (AC5, AC6), acceptance with versioned mandate and exactly-once recurring orders, rejection (AC7), amount edit, pause, ownership check (AC8).
