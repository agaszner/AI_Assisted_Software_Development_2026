# AGENTS.md — SaverAI (school project)

Instructions for AI coding agents (Claude Code, Gemini / Antigravity, Copilot, Codex) and humans working in this repository. Read this file fully before making any change.

## 1. What this project is

SaverAI is a savings assistant for bank customers. The customer fills in a fixed questionnaire, the app analyses past transactions, proposes a savings and investment plan, replays it on the customer's own history ("financial time machine"), and after explicit approval sets up recurring orders. Orders run only within a signed, versioned **mandate**.

This is a university homework project (BME, AI Assisted Software Development). Everything banking-related is **simulated**: transactions, products, returns and order execution.

**The application contains no AI service.** AI tools are used to *develop* it (requirements, implementation, testing — documented in `docs/ai-usage.md`), never inside the running app. An agentic version with an LLM exists as a separate project (`../SaverAI-competition`, Gránit Bank ideas competition). Do not copy agent / LLM code from it into this repository.

**Source of truth for requirements:** `docs/specification.md` (acceptance criteria AC1–AC8), a Markdown mirror of the submitted `docs/SaverAI_BIA823.docx`. Keep the two in sync and the specification under 4,000 characters. If code and specification disagree, the specification wins — stop and flag the conflict instead of silently picking one.

## 2. Golden rules (non-negotiable)

1. **No AI at runtime.** No LLM SDK, model call or AI dependency in `backend/` or `frontend/`. The questionnaire has fixed questions with validated answers.
2. **The rule engine decides everything.** Every amount, date, product choice, risk filter and confidence level comes from the rule engine (`backend/rules/`). Explanations shown to the customer are fixed templates (`backend/plans/explanations.py`) filled only with rule-engine results.
3. **Money is an integer number of forints** (`Huf = int`). Never use `float` for money. Rounding rules live in one place: `backend/rules/money.py`.
4. **The rule engine is pure.** Code in `backend/rules/` must not import Django, the database, the network or the system clock. Inputs in, results out.
5. **Time is injected.** Never call `datetime.now()` / `timezone.now()` in business logic. Use the `Clock` passed in (`backend/core/clock.py`). This is what makes the time machine, event detection and tests deterministic.
6. **No action without the mandate.** Every order execution goes through `rules.mandate.check_action()`; the log entry records the mandate version and clause number that allowed it.
7. **Execution is idempotent.** Accepting or executing the same plan twice must not create duplicates (AC7). Use the idempotency key on `Execution`.
8. **No real data, no real bank, no secrets.** Use the synthetic data generator. Never commit secrets; use `.env` (see `.env.example`).
9. **Documentation is part of the change** (see section 8). A change without its documentation update is not done.

## 3. Tech stack

| Layer | Technology |
| --- | --- |
| Backend framework | Python 3.12, Django 5, Django Ninja (API, Pydantic schemas) |
| Database | SQLite (dev / homework), Django migrations |
| Admin | Django admin (product catalogue, rule parameters) — the "Admin" role |
| Auth | Django auth + session/JWT via Ninja; roles: `customer`, `admin` |
| Scheduling | APScheduler (monthly orders, year-end tax check) |
| Frontend | React + TypeScript (strict) + Vite, Tailwind CSS, TanStack Query, Recharts |
| Tests | pytest, pytest-django, Hypothesis, Playwright (e2e), Vitest (frontend) |
| Quality | ruff (lint + format), mypy, eslint, prettier |
| Run | Docker Compose, Makefile |

Do not add a dependency without an ADR (section 8.3).

## 4. Commands

```bash
make setup        # install backend + frontend deps, create .env from .env.example
make migrate      # apply Django migrations
make seed         # load synthetic personas, products and inflation table
make dev          # run backend (localhost:8000) and frontend (localhost:5173)
make test         # all backend tests (pytest)
make test-fe      # frontend tests (vitest)
make e2e          # Playwright end-to-end tests (needs `make dev` running)
make lint         # ruff, mypy, eslint
make fmt          # auto-fix ruff lint and formatting
make docs-check   # verify traceability and changelog (see section 8.6)
make check        # lint + test + docs-check — run this before every commit
```

Docker alternative: `docker compose up --build`.

Environment variables (`.env.example`): `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `SAVERAI_FIXED_DATE` (freeze today's date for demos), `SEED_PASSWORD` (demo user password).

## 5. Repository layout

```
backend/
  config/            Django settings, urls
  core/              Clock, money types, shared utilities
  rules/             PURE rule engine — no Django imports
    surplus.py         median monthly surplus, monthly amount
    plan.py            priority allocation, product filtering
    backtest.py        financial time machine (nominal + real value)
    confidence.py      confidence level from data quantity / volatility
    mandate.py         mandate schema + check_action()
    events.py          raise / bonus / outlier detection
    tax.py             pension tax-credit headroom
    whatif.py          what-if scenarios
  banking/           Django app: accounts, transactions, products, orders (simulated)
  plans/             Django app: questionnaire answers, plans, mandates, executions, log
    explanations.py    fixed explanation templates filled from rule results
  api/               Django Ninja routers and schemas (incl. questionnaire)
  tests/
    rules/             unit + property tests for the rule engine
    api/               endpoint, auth and validation tests
    regression/        change-request regression and data-preservation tests
    defects/           faulty vs fixed versions (homework requirement, do not "fix")
frontend/
  src/screens/       one folder per screen (matches Figma 01–10)
  src/components/    shared UI (Button, TransactionRow, SideNav)
  src/theme/         design tokens exported from Figma variables
docs/                see section 8
AGENTS.md            this file (CLAUDE.md and GEMINI.md are symlinks to it)
CHANGELOG.md
README.md
```

## 6. Architecture rules

- Dependency direction: `api` → `plans` / `banking` (services) → `rules`. Never the other way.
- `rules/` functions take plain dataclasses / Pydantic models and return results; they never read the DB.
- Ninja schemas (`api/schemas.py`) validate all input, including every questionnaire answer. Invalid input returns 422 with a clear message; access to another customer's data returns 403 (AC8).
- Explanation templates only format values from a rule result; they never compute.
- Rule parameters (70%, 3 months, 12 months, 100,000 HUF, tax limits) live in the `RuleConfig` model, editable in Django admin, with defaults in `rules/defaults.py`. Never hard-code them elsewhere.

## 7. Coding and testing conventions

**Python:** full type hints, mypy clean, ruff formatted. Small functions, descriptive names, docstrings on public rule functions stating inputs, outputs and the AC they implement.

**TypeScript:** `strict` mode, no `any`. Colors and spacing only from `src/theme/` tokens. Every interactive element has a 44 px minimum touch target and an accessible label.

**Tests:**

- Every acceptance criterion has at least one automated test named `test_acN_<behaviour>` (e.g. `test_ac1_median_surplus_gives_73500`).
- Each AC needs normal, edge and invalid/unauthorised cases where they apply.
- Rule engine invariants get Hypothesis property tests (e.g. "balance never drops below the mandate minimum for any transaction sequence").
- Never edit or delete a failing test to make it pass. If a test is wrong, explain why in the commit message and the AI usage log.
- `tests/defects/` contains intentionally faulty versions with their failing test runs. Do not modify these.

## 8. Continuous documentation

Documentation is updated **in the same commit** as the code it describes. An agent finishing a task must state which documents it updated, or explicitly why none needed updating.

### 8.1 What to update when

| You changed… | Update |
| --- | --- |
| Behaviour covered by an AC | `docs/specification.md` + `docs/SaverAI_BIA823.docx` (if the requirement changed) and `docs/traceability.md` |
| Added / renamed a test | `docs/traceability.md` |
| An architectural choice or dependency | new ADR in `docs/decisions/` |
| Anything user-visible or behavioural | `CHANGELOG.md` under `## [Unreleased]` |
| Setup, commands, env variables | `README.md` and section 4 of this file |
| Used AI for a substantive decision | `docs/ai-usage.md` (section 8.4) |
| Data model / migration | `docs/architecture.md` (data model section) |
| Change-request work | `docs/change-request.md` |
| Finished an item listed in `docs/tasks.md` | tick it (`- [X]`) in `docs/tasks.md` |

### 8.2 `docs/traceability.md`

One table, kept current. Every AC must have at least one row.

```markdown
| AC | Requirement (short) | Verification | Test / evidence | Status |
| --- | --- | --- | --- | --- |
| AC1 | Median surplus → monthly amount | automated | tests/rules/test_surplus.py::test_ac1_median_surplus_gives_73500 | passing |
| AC5 | No surplus → no plan | automated + manual | tests/api/test_plans.py::test_ac5_no_surplus; manual steps in docs/manual-checks.md#ac5 | passing |
```

Manual checks go in `docs/manual-checks.md` with reproducible steps and the expected result.

### 8.3 Architecture Decision Records — `docs/decisions/NNNN-short-title.md`

```markdown
# NNNN. Title
Date: YYYY-MM-DD · Status: proposed | accepted | superseded by NNNN

## Context
## Decision
## Alternatives considered
## Consequences
```

Never edit an accepted ADR's decision; supersede it with a new one.

### 8.4 AI usage log — `docs/ai-usage.md`

The homework requires AI use in at least three development phases and three documented decision cases. When an AI tool's suggestion leads to a substantive decision (accepted, modified or rejected), add an entry. Agents may draft the entry; the human author verifies and completes it.

```markdown
### Case N — short title
- Phase: requirements | design | implementation | testing | change request
- Tool and model:
- Problem:
- Context given and key instruction:
- Essence of the AI suggestion:
- Decision (accepted / modified / rejected) and technical reasons:
- Verification: link to test, commit or execution result
- Limitations of this verification:
```

### 8.5 `CHANGELOG.md`

Follow *Keep a Changelog*. Sections: Added, Changed, Fixed, Removed. Reference AC numbers and ADRs, e.g. `- Time machine flags skipped months (AC4, ADR-0004)`. Tag `v1.0-first-version` at milestone 2 and `v2.0-final` at milestone 3.

### 8.6 Docs check

`make docs-check` fails if an AC in `docs/specification.md` has no row in `docs/traceability.md`, if a test referenced in the traceability table does not exist, or if code under `backend/` or `frontend/src/` changed without a `CHANGELOG.md` change. Run it before committing.

## 9. Workflow for agents

1. Read the task, the relevant ACs in `docs/specification.md` and related ADRs.
2. State a short plan: files to touch, tests to add, docs to update. Wait for approval if the task changes a requirement, the data model or adds a dependency.
3. Write or update the test first where practical, then the code.
4. Run `make check`. Do not finish with failing checks.
5. Update documentation (section 8), and tick every finished item in `docs/tasks.md`.
6. Commit with Conventional Commits: `feat(rules): flag skipped months in backtest (AC4)`.
7. End with a summary: what changed, which ACs are affected, test results, docs updated, open questions.

## 10. Change request protocol (milestone 3)

1. Start from tag `v1.0-first-version` on a branch `change-request/<short-name>`.
2. Write `docs/change-request.md` first: the new requirement, affected ACs, affected code sections, chosen solution and why.
3. Update `docs/specification.md` and mark changed ACs.
4. Data model changes go through a new migration; never edit an applied one. Add a data-preservation test in `tests/regression/` that loads data created by the old schema and checks it survives.
5. Add regression tests proving existing behaviour is unchanged.

## 11. Dual implementation (homework requirement)

One feature (default: the time machine in `rules/backtest.py`) is implemented twice with two different AI tools, on branches `dual/claude-code` and `dual/gemini`, from the same prompt and the same tests. Results and the comparison go in `docs/dual-implementation.md`. Only one version is merged; the other stays on its branch.

## 12. Do not

- Add an LLM, AI SDK, model API key or any call to an AI service to the application.
- Copy agent / LLM code from the competition project.
- Call real banking APIs or the system clock in business logic.
- Use `float` for money.
- Disable, skip or loosen tests or the mandate check to get something working.
- Modify `tests/defects/`, applied migrations or accepted ADRs.
- Commit secrets, real personal data or generated build output.
- Finish a task without updating documentation.
