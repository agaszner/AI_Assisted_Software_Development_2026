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
- API: `GET /api/account` (server date, balance, minimum balance, 5 newest transactions), `GET /api/rules` (plan rules filled from `RuleConfig`) and `GET /api/plans/{id}/mandate` (mandate terms and clauses, preview before acceptance); another customer's mandate returns 403 (AC8).
- API details for the web UI: plan date, risk score, share, minimum balance, next transfer, mandate version and saved total; per-item due date and progress; spending-analysis median working and no-surplus / too-little-data explanations; time machine transfer counts (AC4–AC6).
- Questionnaire errors name the field (`{"detail", "field"}`), e.g. a past expense date (AC8).
- Plan revision: `POST /api/plans/{id}/revise` proposes a new amount for the active plan; signing it pauses the old plan and signs the next mandate version (ADR-0004, migration 0002).
- API: `GET /api/activity`, the execution log with scheduled transfers, audit fields (mandate version, clause, idempotency key) and plan events; log entries store the amount (migration 0003) (AC6, AC7).
- Frontend API client: typed mirror of the API schemas, CSRF token read on every request, readable messages for 403 / 409 / 422 errors and the field a 422 names.
- Frontend design tokens copied from the Figma variables (colours, spacing, radii, Focus/Ring, Elevation/Panel, text styles, Inter) and base components: Icon, Button, Badge, TextField, Checkbox, ErrorMessage, Card, StatTile, Kbd, ProgressBar (44 px targets, labelled controls, visible focus).
- Frontend layouts from Figma: SideNav and AppShell (drawer below 1024 px), FlowHeader / FlowLayout (Step N of 4, Back, Save & exit), sticky SummaryPanel (bottom bar below 1024 px) and an accessible Modal (focus trap, Esc).
- Frontend login screen (Figma 01), protected routes and the sidebar layout; an expired session (401) returns the customer to login.
- Home screen (Figma 02): balance, minimum balance and next transfer, savings plan progress from the API, recent transactions, rule summary from RuleConfig.

### Changed
- Frontend target is a responsive web UI instead of a mobile UI: left sidebar, focused plan flow, sticky summary panel, password-confirmation modal, execution log table; new Figma file (AI usage case 3).
- Signing a mandate (`POST /api/plans/{id}/accept`) requires the customer's password; a wrong password signs nothing (AC7, ADR-0004).

