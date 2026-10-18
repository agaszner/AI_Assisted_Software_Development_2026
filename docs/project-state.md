# Project state — M2 first working version

Milestone 2 of the homework (`docs/Homework_requirements_EN.pdf`): "submit the source code implementing
the main user workflow, setup instructions and basic tests. Document the project state and development
history in a public GitHub repository." This file is that state report. It links to the detailed
documents instead of repeating them.

- Repository: https://github.com/agaszner/AI_Assisted_Software_Development_2026
- Specification: [`docs/specification.md`](specification.md) (AC1–AC8, 3,768 characters).

## 1. Main user workflow — what works end to end

The customer flow from the specification runs from the browser to the database:

1. **Login** (Figma 01) with a seeded persona; roles `customer` and `admin`.
2. **Home** (02): balance, 100,000 HUF minimum balance, next transfer, recent transactions, plan rules.
3. **Questionnaire** (03): fixed questions, risk score, emergency fund, planned expenses. Amounts are
   whole forints; a negative amount or past date returns 422 and is shown at the field (AC8).
4. **Spending analysis** (04): median monthly surplus of the last 6 months and the 70 % suggested
   amount (AC1).
5. **Plan review** (05, 05b): priority-ordered items (emergency fund → planned expenses → investment,
   AC2, AC3), confidence level (AC6), lower the amount or reject (AC7).
6. **Time machine** (06): the plan replayed on the last 12 months, skipped months flagged (AC4).
7. **Mandate** (07, 07b): terms and numbered clauses, consent, password confirmation; signing creates
   the recurring orders exactly once (AC7, ADR-0004).
8. **Active plan and Activity** (08): recurring orders, execution log with mandate version, clause and
   idempotency key, transfer approval for low-confidence plans (AC6), pause, change amount as the next
   mandate version.
9. **Explanation states**: no surplus (09, AC5) and too little data (10, AC6) instead of a plan.

Monthly orders run with `manage.py run_orders [--period YYYY-MM]`. Every execution passes
`rules.mandate.check_action()` and is idempotent per order and month (AC7). The Admin role edits the
product catalogue and rule parameters (`RuleConfig`) in Django admin.

Demo personas from `make seed`: `anna` (AC1, AC2), `bence` (AC5), `csilla` (AC6, 2 months),
`dani` (AC6, 4 months), `admin`. See the persona table in [`README.md`](../README.md).

Architecture and data model: [`docs/architecture.md`](architecture.md). Tech stack: Django 5 +
Django Ninja, SQLite, React + TypeScript + Vite (ADR-0001, ADR-0003). The application contains no AI
service; all amounts and decisions come from the pure rule engine in `backend/rules/`.

## 2. Setup instructions

Full instructions are in [`README.md`](../README.md). Short version:

```bash
make setup && make migrate && make seed
make dev          # backend http://localhost:8000, app http://localhost:5173
```

Docker alternative: `docker compose up --build`, then
`docker compose exec backend uv run python manage.py seed`.

## 3. Tests and results

Run on 2026-10-18 at `6051eac`:

| Command | Result |
| --- | --- |
| `make lint` | ruff, ruff format, mypy (69 files), eslint, tsc, prettier: clean |
| `make test` | 166 backend tests passed (pytest, incl. Hypothesis property tests) |
| `make test-fe` | 96 frontend tests passed in 16 files (Vitest) |
| `make docs-check` | OK (every AC has a traceability row, every referenced test exists) |
| Defect demo | `[faulty]` fails with `assert 133333 == 105000`, `[fixed]` passes |
| `make e2e` | Not run in this check (it resets the local database); run it before tagging |

Every acceptance criterion has automated tests; the full mapping (AC → test → status) is in
[`docs/traceability.md`](traceability.md). Manual UI checks with steps and expected results are in
[`docs/manual-checks.md`](manual-checks.md).

Required test cases from the assessment guide:

| Case | Example |
| --- | --- |
| Normal | AC1 `tests/rules/test_surplus.py::test_ac1_median_surplus_gives_73500` |
| Edge 1 | AC4 `tests/rules/test_backtest.py::test_ac4_month_breaking_minimum_is_flagged_skipped` |
| Edge 2 | AC6 `tests/rules/test_confidence.py::test_ac6_two_months_gives_no_estimate`, `test_ac6_four_months_is_low_confidence` |
| Invalid input | AC8 `tests/api/test_plans_api.py::test_ac8_negative_amount_is_rejected`, `test_ac8_past_expense_date_is_rejected` (422) |
| Unauthorised | AC8 `tests/api/test_plans_api.py::test_ac8_other_customer_cannot_view_or_accept_plan` (403) |
| Regression | AC7 `tests/services/test_acceptance.py::test_ac7_accepting_twice_creates_orders_once`, `tests/services/test_execution.py::test_ac7_running_orders_twice_executes_once` |
| Faulty vs fixed | AC1 mean instead of median, deliberately introduced: [`backend/tests/defects/README.md`](../backend/tests/defects/README.md), outputs `run_faulty.txt`, `run_fixed.txt` |
| End to end | `frontend/e2e/main-flow.spec.ts`: main flow (anna) and no-surplus path (bence) |

Rule-engine invariants are also covered by Hypothesis property tests: the balance never drops below
the mandate minimum (time machine and mandate check).

## 4. Development history

37 commits between 2026-10-06 and 2026-10-12 (`git log`). Phases:

| Dates | Phase | Main commits |
| --- | --- | --- |
| 10-06 | Specification, agent instructions, implementation plans | `870d66f` init and specification, `d21e922` AGENTS.md, `40b8f6f` backend plan, `8294218` frontend plan |
| 10-06 – 10-07 | Backend skeleton and pure rule engine | `f554851` Django skeleton, `d59d4f1` clock and money, `6098d42` surplus (AC1, AC5), `2a91274` confidence (AC6), `2e040e2` allocation (AC2, AC3), `1278137` time machine (AC4), `ce34168` mandate check |
| 10-07 – 10-08 | Data model, services, API | `a9ffea9` seed, `5161d46` proposal and acceptance, `4115671` idempotent execution (AC7), `b658b8a` customer endpoints with validation and ownership checks (AC8) |
| 10-08 – 10-10 | UI redesign and frontend foundation | `7077435` responsive web redesign (AI usage Case 3), `cf221f4` Figma-based frontend plan, `7712e78` Vite skeleton, `183c96e` password signing and plan revision (ADR-0004), `0c8cabc` API client, tokens, login, home |
| 10-10 – 10-11 | Frontend screens and dual implementation | `a09afc2` questionnaire to plan review; time machine built twice: `dual/claude` (`ab4f64b`, Claude Code) and `dual/gemini` (`f9dd2f9`, Antigravity); `dual/claude` merged with follow-up `41825d4`; comparison in [`docs/dual-implementation.md`](dual-implementation.md) |
| 10-11 – 10-12 | Remaining screens, e2e, defect demo, docs, Docker | `5474c34` mandate, active plan, activity; `ba9fb0b` Playwright; `8764432` AC1 defect; `edc4c57` docs; `6051eac` frontend Docker service |

Branches: `main` (submitted line), `dual/base`, `dual/claude`, `dual/gemini` (kept for the dual
implementation comparison), `backend` and `implement_time_machine_screen` (working branches).
User-visible changes are listed in [`CHANGELOG.md`](../CHANGELOG.md); decisions in
[`docs/decisions/`](decisions/) (ADR-0001 to ADR-0004).

## 5. AI-assisted development

- Agent instructions: [`AGENTS.md`](../AGENTS.md), with `CLAUDE.md` and `GEMINI.md` as symlinks, so
  Claude Code and Antigravity follow the same rules.
- Implementation plans written with Claude Code: `docs/superpowers/plans/`.
- Decision cases: [`docs/ai-usage.md`](ai-usage.md), Cases 1–4 (design: framework, idempotency,
  UI target; implementation: password signing).
- Dual implementation of the time machine screen (AC4): [`docs/dual-implementation.md`](dual-implementation.md).