# SaverAI Backend (M2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Commits:** the user asked for **no commits**. Every task ends with a *suggested* Conventional Commit message; the user runs `git commit` themselves. Do not run `git commit`, `git tag` or `git push`. If the user later says to commit, replace each "Suggested commit" step with a real commit.

**Goal:** Build the M2 backend of SaverAI: a pure rule engine (AC1–AC6), Django models and services for plans, mandates and idempotent order execution (AC7), and a Django Ninja API with validation and ownership checks (AC8). The frontend is covered by a separate plan.

**Architecture:** `api` (Django Ninja) → `plans` / `banking` (Django apps, services) → `rules` (pure Python, no Django). Every number shown to the customer comes from `rules/`. Time is injected through `core.clock.Clock`. Money is `int` forints everywhere.

**Tech Stack:** Python 3.12, uv, Django 5.2, Django Ninja 1.x (Pydantic 2), SQLite, pytest + pytest-django + Hypothesis, ruff, mypy (strict) + django-stubs.

**Spec:** `docs/specification.md` (AC1–AC8). Also read `AGENTS.md` (golden rules, layout, documentation rules) and `docs/tasks.md` (M2 task list). If code and spec disagree, the spec wins: stop and flag it.

## Global Constraints

- No AI at runtime: no LLM SDK, model call or AI dependency in `backend/`.
- The rule engine decides everything: amounts, dates, products, risk filters, confidence. Explanations are fixed templates filled with rule results.
- Money is `Huf = int`. Never `float`. All rounding lives in `backend/rules/money.py` (always rounds down to whole forints).
- `backend/rules/` imports no Django, DB, network or system clock (enforced by `tests/rules/test_purity.py`).
- Never call `datetime.now()`, `date.today()` or `timezone.now()` in business logic. Use `core.clock.get_clock()` / the `Clock` argument. Only `core/clock.py` reads the system clock.
- Every order execution goes through `rules.mandate.check_action()`; the log stores mandate version and clause.
- Accepting and executing are idempotent (AC7): DB unique constraints back every "exactly once".
- Rule parameters live in `RuleConfig` (defaults in `rules/defaults.py`); never hard-code 70, 3, 6, 12 or 100,000 elsewhere.
- Spec values: monthly amount = **70 %** of the median monthly surplus of the last **6** months; emergency fund = **3×** median monthly expenses; money needed within **12** months → low-risk liquid products only; transfer that would push balance below **100,000 HUF** is skipped; < **3** months of data → no estimate; **3–5** months → low confidence + per-transfer approval; time machine replays **12** months.
- Test names for AC tests: `test_acN_<behaviour>`. Never edit or delete a failing test to make it pass.
- Every task updates `CHANGELOG.md` (`## [Unreleased]`) and `docs/traceability.md` in the same change (AGENTS.md section 8). `make docs-check` fails otherwise.
- No new dependency beyond the list in ADR-0001 (Task 1).

## Review Focus

Spec-silent inputs most likely to hurt a real user. Each has a pinned test in the owning task.

1. A calendar month with **no transactions** between the first data month and last month → counts as 0 surplus, not dropped from the median (Task 4: `test_month_without_transactions_counts_as_zero_surplus`).
2. "Today" is **mid-month** → the current partial month never counts for the surplus or the time machine, but its transactions still shift the opening balance (Task 4: `test_ac1_current_partial_month_is_ignored`; Task 7: `test_ac4_current_month_only_shifts_opening_balance`).
3. A planned expense **due this month** (0 months away) → no division by zero; the full amount is needed now (Task 6: `test_expense_due_this_month_needs_full_amount_now`).
4. Admin **deactivates every eligible product** → clear 409 message, never a 500 (Task 6: `test_no_eligible_product_raises`; Task 11: `test_no_eligible_product_is_a_conflict`).
5. Money sent as **float, string or bool** in JSON (e.g. `100.0`, `"100"`) → 422, never silently coerced (Task 13: `test_ac8_non_integer_amount_is_rejected`).

## Interpretations, deviations and deferrals

Recorded in `docs/decisions/0002-backend-rule-interpretations.md` (Task 2). The user approves them by approving this plan.

- **AC5 boundary:** median surplus `<= 0` → no plan (spec says `< 0`; a median of exactly 0 gives a 0 HUF amount, so there is nothing to plan).
- **AC6 < 3 months:** the plan is built only from the customer-entered expected monthly savings; confidence is `none` and every transfer needs approval, like `low`.
- **Low-risk** = risk level `<= low_risk_max` (new `RuleConfig` parameter, default 2) and never above the customer's risk score.
- **Separate parameters** for values the spec reuses: `min_months_for_estimate` (3) vs `emergency_fund_months` (3); `liquid_horizon_months` (12) vs `backtest_months` (12); `surplus_window_months` (6) vs `full_confidence_months` (6).
- **Allocation:** emergency fund gets `min(amount, gap)`; planned expenses (by due date) get `ceil(amount / months left)`; the rest goes to long-term investment. Product choice: riskiest eligible product, ties → lowest id.
- **Time machine:** principal only (no product returns, no inflation); the transfer happens at month end after that month's transactions; leaving exactly 100,000 HUF is allowed.
- **Recurring orders live in `plans.RecurringOrder`**, not `banking.Order` as `docs/tasks.md` says, so `banking` never depends on `plans`.
- **Scheduling:** management command `run_orders`; APScheduler is deferred (no dependency added in M2).
- **Deferred:** `rules/events.py`, `rules/tax.py`, `rules/whatif.py`, inflation table in `make seed`, volatility in confidence, frontend Makefile targets (`test-fe`, `e2e`, eslint in `lint`) — added by the frontend plan.
- **Login endpoint is CSRF-exempt** (Django Ninja default for unauthenticated operations); all session-authenticated endpoints check CSRF.

## File map

```
Makefile                                  Task 1, 2, 10
.env.example                              Task 1
README.md                                 Task 1, 14
CHANGELOG.md                              every task
scripts/docs_check.py                     Task 2
docs/decisions/0001-tech-stack.md         Task 1
docs/decisions/0002-backend-rule-interpretations.md   Task 2
docs/traceability.md                      Task 2, then every AC task
docs/architecture.md                      Task 9
docs/manual-checks.md                     Task 14
docs/ai-usage.md                          Task 14 (draft entry)
backend/pyproject.toml, uv.lock           Task 1
backend/manage.py                         Task 1
backend/config/{__init__,settings,urls}.py           Task 1
backend/core/clock.py                     Task 3
backend/rules/__init__.py                 Task 3
backend/rules/money.py                    Task 3   Huf, percent_of, median, ceil_div
backend/rules/months.py                   Task 3   month_of, add_months, months_between
backend/rules/defaults.py                 Task 3   RuleParams, DEFAULTS
backend/rules/types.py                    Task 3   Txn, ProductInfo, PlannedExpense
backend/rules/surplus.py                  Task 4   AC1, AC5
backend/banking/synthetic.py              Task 4   pure synthetic transaction generator
backend/rules/confidence.py               Task 5   AC6
backend/rules/plan.py                     Task 6   AC2, AC3, AC5, AC6
backend/rules/backtest.py                 Task 7   AC4
backend/rules/mandate.py                  Task 8   check_action
backend/banking/models.py, admin.py       Task 9
backend/plans/models.py, admin.py         Task 9
backend/banking/management/commands/seed.py          Task 10
backend/plans/explanations.py             Task 11
backend/plans/services.py                 Task 11  AC5–AC8 service side
backend/plans/execution.py                Task 12
backend/plans/management/commands/run_orders.py      Task 12
backend/api/{api,auth,schemas,routes}.py  Task 1 (api, auth), Task 13
backend/tests/...                         every task
```

---

### Task 1: Backend skeleton, tooling, auth smoke test, ADR-0001

Deliverable: `make lint` and `make test` are green on a Django + Ninja skeleton with session login. This task verifies the framework assumptions (Ninja `django_auth` → 401, mypy strict + django-stubs) that later tasks rely on.

**Files:**
- Create: `backend/pyproject.toml`, `backend/manage.py`, `backend/config/__init__.py`, `backend/config/settings.py`, `backend/config/urls.py`
- Create: `backend/core/__init__.py`, `backend/banking/__init__.py`, `backend/banking/models.py`, `backend/plans/__init__.py`, `backend/plans/models.py`
- Create: `backend/api/__init__.py`, `backend/api/api.py`, `backend/api/auth.py`
- Create: `backend/tests/__init__.py`, `backend/tests/api/__init__.py`, `backend/tests/api/test_auth.py`
- Create: `Makefile`, `.env.example`, `README.md`, `CHANGELOG.md`, `docs/decisions/0001-tech-stack.md`
- Modify: `AGENTS.md` (section 4: `make fmt`, env variables)

**Interfaces:**
- Produces: `api.auth.current_user(request: HttpRequest) -> User`; `api.api.api: NinjaAPI` (session auth by default); settings attribute `SAVERAI_FIXED_DATE: str | None`; Make targets `setup`, `migrate`, `dev`, `test`, `lint`, `fmt`, `check`.

- [ ] **Step 1: Write ADR-0001 (dependency approval record)**

Create `docs/decisions/0001-tech-stack.md`:

```markdown
# 0001. Backend tech stack and dependencies
Date: 2026-10-06 · Status: proposed

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
```

- [ ] **Step 2: Create `backend/pyproject.toml`**

```toml
[project]
name = "saverai-backend"
version = "0.1.0"
description = "SaverAI backend: rule engine, simulated bank, plans API"
requires-python = ">=3.12,<3.13"
dependencies = [
  "django>=5.2,<6",
  "django-ninja>=1.4,<2",
]

[dependency-groups]
dev = [
  "pytest>=8",
  "pytest-django>=4.9",
  "hypothesis>=6.100",
  "ruff>=0.6",
  "mypy>=1.11",
  "django-stubs[compatible-mypy]>=5.1",
]

[tool.uv]
package = false

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
pythonpath = ["."]
testpaths = ["tests"]
addopts = "-q"

[tool.ruff]
line-length = 100
target-version = "py312"
extend-exclude = ["*/migrations/*"]

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "DTZ"]

[tool.ruff.lint.per-file-ignores]
"core/clock.py" = ["DTZ"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["mypy_django_plugin.main"]
exclude = ["/migrations/"]

[tool.django-stubs]
django_settings_module = "config.settings"

# Django's ModelAdmin is not subscriptable at runtime, so admin modules use the bare class.
[[tool.mypy.overrides]]
module = ["banking.admin", "plans.admin"]
disallow_any_generics = false
```

`DTZ` makes ruff flag `datetime.now()` / `date.today()` everywhere except `core/clock.py` (golden rule 5).

- [ ] **Step 3: Create Django project files**

`backend/manage.py`:

```python
#!/usr/bin/env python
"""Django command-line entry point."""

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
```

`backend/config/__init__.py`, `backend/core/__init__.py`, `backend/api/__init__.py`, `backend/banking/__init__.py`, `backend/plans/__init__.py`, `backend/tests/__init__.py`, `backend/tests/api/__init__.py`: empty files.

`backend/banking/models.py`:

```python
"""Simulated bank models. Filled in by Task 9."""
```

`backend/plans/models.py`:

```python
"""Plan models. Filled in by Task 9."""
```

`backend/config/settings.py`:

```python
"""Django settings for SaverAI. Values come from environment variables (see .env.example)."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "banking",
    "plans",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Budapest"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"

# The Vite dev server (frontend plan) calls the API from this origin.
CSRF_TRUSTED_ORIGINS = ["http://localhost:5173"]

# Freeze "today" (ISO date) for demos and tests. Empty = real date. Read only via core.clock.get_clock().
SAVERAI_FIXED_DATE: str | None = os.environ.get("SAVERAI_FIXED_DATE") or None
```

`backend/config/urls.py`:

```python
"""URL routes: Django admin (Admin role) and the JSON API."""

from django.contrib import admin
from django.urls import path

from api.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
```

- [ ] **Step 4: Write the failing auth tests**

`backend/tests/api/test_auth.py`:

```python
import pytest
from django.contrib.auth.models import User
from django.test import Client

pytestmark = pytest.mark.django_db


def login(client: Client, username: str, password: str) -> int:
    response = client.post(
        "/api/auth/login",
        {"username": username, "password": password},
        content_type="application/json",
    )
    return response.status_code


def test_me_requires_login(client: Client) -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_me_returns_customer_role(client: Client) -> None:
    client.force_login(User.objects.create_user(username="anna", password="pw"))
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json() == {"username": "anna", "role": "customer"}


def test_staff_user_has_admin_role(client: Client) -> None:
    client.force_login(User.objects.create_user(username="boss", password="pw", is_staff=True))
    assert client.get("/api/auth/me").json()["role"] == "admin"


def test_login_with_wrong_password_is_rejected(client: Client) -> None:
    User.objects.create_user(username="anna", password="pw")
    assert login(client, "anna", "wrong") == 401


def test_login_then_logout(client: Client) -> None:
    User.objects.create_user(username="anna", password="pw")
    assert login(client, "anna", "pw") == 200
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_csrf_endpoint_sets_token(client: Client) -> None:
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200
    assert response.json()["csrftoken"]
```

- [ ] **Step 5: Install and run tests to verify they fail**

Run: `cd backend && uv sync && uv run pytest tests/api/test_auth.py`
Expected: FAIL / collection error: `ModuleNotFoundError: No module named 'api.api'`.

- [ ] **Step 6: Implement auth router and API**

`backend/api/auth.py`:

```python
"""Login, logout and current user. Roles: `admin` = Django staff user, otherwise `customer`."""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.middleware.csrf import get_token
from ninja import Router, Schema
from ninja.errors import HttpError

router = Router(tags=["auth"])


class LoginIn(Schema):
    username: str
    password: str


class MeOut(Schema):
    username: str
    role: str


def current_user(request: HttpRequest) -> User:
    """Return the logged-in user. Ninja's django_auth has already rejected anonymous requests."""
    user = request.user
    if not isinstance(user, User):
        raise HttpError(401, "Not authenticated.")
    return user


def _me(user: User) -> MeOut:
    return MeOut(username=user.username, role="admin" if user.is_staff else "customer")


@router.get("/csrf", auth=None)
def csrf(request: HttpRequest) -> dict[str, str]:
    """Set the CSRF cookie for the frontend and return the token."""
    return {"csrftoken": get_token(request)}


@router.post("/login", auth=None, response=MeOut)
def login_view(request: HttpRequest, payload: LoginIn) -> MeOut:
    user = authenticate(request, username=payload.username, password=payload.password)
    if not isinstance(user, User):
        raise HttpError(401, "Invalid username or password.")
    login(request, user)
    return _me(user)


@router.post("/logout")
def logout_view(request: HttpRequest) -> dict[str, bool]:
    logout(request)
    return {"ok": True}


@router.get("/me", response=MeOut)
def me(request: HttpRequest) -> MeOut:
    return _me(current_user(request))
```

`backend/api/api.py`:

```python
"""The Django Ninja API. Every endpoint needs a session login unless it sets auth=None."""

from ninja import NinjaAPI
from ninja.security import django_auth

from api.auth import router as auth_router

api = NinjaAPI(title="SaverAI", auth=django_auth)
api.add_router("/auth", auth_router)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/api/test_auth.py -v`
Expected: 6 passed. If `test_me_requires_login` returns something other than 401, stop: later tasks assume Ninja's `django_auth` gives 401.

- [ ] **Step 8: Makefile, `.env.example`, README, CHANGELOG**

`Makefile` (recipe lines start with a TAB):

```make
# SaverAI commands (AGENTS.md section 4). Frontend targets are added by the frontend plan.
-include .env
export

.PHONY: setup migrate dev test lint fmt check

setup:
	test -f .env || cp .env.example .env
	cd backend && uv sync

migrate:
	cd backend && uv run python manage.py migrate

dev:
	cd backend && uv run python manage.py runserver 8000

test:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy .

fmt:
	cd backend && uv run ruff check --fix . && uv run ruff format .

check: lint test
```

`.env.example`:

```
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=1
# Optional: freeze "today" for demos, e.g. 2026-10-06. Empty = real date.
SAVERAI_FIXED_DATE=
# Password for the seeded demo users (make seed). Choose your own.
SEED_PASSWORD=change-me
```

`README.md`:

```markdown
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

## Quality
    make test       # pytest
    make lint       # ruff + mypy
    make fmt        # auto-fix lint and formatting
    make check      # run before every commit

Specification: `docs/specification.md`. Agent instructions: `AGENTS.md`.
```

`CHANGELOG.md`:

```markdown
# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Django 5 + Django Ninja backend skeleton with session login, `customer` / `admin` roles and a Makefile (ADR-0001).
```

In `AGENTS.md` section 4 (AGENTS.md 8.1: commands and env variables), add this line after `make lint`:

```bash
make fmt          # auto-fix ruff lint and formatting
```

and add below the code block: "Environment variables (`.env.example`): `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `SAVERAI_FIXED_DATE` (freeze today's date for demos), `SEED_PASSWORD` (demo user password)."

- [ ] **Step 9: Run lint and full tests**

Run: `make fmt && make check`
Expected: ruff clean, `Success: no issues found` from mypy, 6 passed. Fix type errors without changing behaviour.

- [ ] **Step 10: Suggested commit (user commits)**

`feat(backend): django ninja skeleton with session auth (ADR-0001)`

---

### Task 2: Docs check, traceability table, ADR-0002

Deliverable: `make docs-check` runs and is green. Rows with status `planned` skip the "test exists" check, so `make check` stays green while ACs land one by one. Later tasks flip rows to `passing`.

**Files:**
- Create: `scripts/docs_check.py`, `docs/traceability.md`, `docs/decisions/0002-backend-rule-interpretations.md`
- Modify: `Makefile`, `CHANGELOG.md`

**Interfaces:**
- Produces: `make docs-check`; traceability row format `| ACn | requirement | verification | evidence | status |` with status `planned` or `passing`; test references are paths relative to `backend/`, e.g. `tests/rules/test_surplus.py::test_ac1_median_surplus_gives_73500`.

- [ ] **Step 1: Write the docs check script**

`scripts/docs_check.py`:

```python
#!/usr/bin/env python3
"""Documentation consistency check (AGENTS.md section 8.6). Standard library only.

Fails when:
- an AC in docs/specification.md has no row in docs/traceability.md;
- a row whose status is not "planned" references a test that does not exist
  (paths are relative to backend/);
- files under backend/ or frontend/src/ have uncommitted changes but CHANGELOG.md has none.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
TEST_REF = re.compile(r"tests/[\w/]+\.py(?:::\w+)?")


def spec_acs() -> set[str]:
    return set(re.findall(r"\*\*(AC\d+)\*\*", (ROOT / "docs/specification.md").read_text()))


def traceability_rows() -> list[tuple[str, str, str]]:
    """Return (ac, evidence, status) for every AC row of the traceability table."""
    rows = []
    for line in (ROOT / "docs/traceability.md").read_text().splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 5 and re.fullmatch(r"AC\d+", cells[0]):
            rows.append((cells[0], cells[3], cells[4]))
    return rows


def test_reference_exists(ref: str) -> bool:
    path, _, name = ref.partition("::")
    file = BACKEND / path
    if not file.is_file():
        return False
    pattern = rf"^\s*def {re.escape(name)}\("
    return not name or re.search(pattern, file.read_text(), re.MULTILINE) is not None


def changed_paths() -> set[str]:
    out = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return {line[3:].split(" -> ")[-1] for line in out.splitlines()}


def main() -> int:
    errors = []
    rows = traceability_rows()
    for ac in sorted(spec_acs() - {row[0] for row in rows}, key=lambda a: int(a[2:])):
        errors.append(f"{ac} has no row in docs/traceability.md")
    for ac, evidence, status in rows:
        if status == "planned":
            continue
        for ref in TEST_REF.findall(evidence):
            if not test_reference_exists(ref):
                errors.append(f"{ac}: referenced test not found: {ref}")
    changed = changed_paths()
    code_changed = any(p.startswith(("backend/", "frontend/src/")) for p in changed)
    if code_changed and "CHANGELOG.md" not in changed:
        errors.append("backend/ or frontend/src/ changed without a CHANGELOG.md change")
    for error in errors:
        print(f"docs-check: {error}", file=sys.stderr)
    if not errors:
        print("docs-check: OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
```

Limitation (write it in the script's docstring if you change it): the CHANGELOG rule only sees uncommitted changes, so it checks the change about to be committed.

- [ ] **Step 2: Run it to verify it fails (no traceability file yet)**

Run: `python3 scripts/docs_check.py`
Expected: FAIL with `FileNotFoundError` for `docs/traceability.md`.

- [ ] **Step 3: Create `docs/traceability.md`**

```markdown
# Traceability

One row per acceptance criterion (`docs/specification.md`). Test paths are relative to `backend/`.
Status: `planned` (test not written yet) or `passing`. `make docs-check` verifies that every AC has
a row and that every test referenced by a non-planned row exists.

| AC | Requirement (short) | Verification | Test / evidence | Status |
| --- | --- | --- | --- | --- |
| AC1 | Median surplus → 70 % monthly amount (73,500) | automated | tests/rules/test_surplus.py::test_ac1_median_surplus_gives_73500 | planned |
| AC2 | Emergency fund filled before any investment | automated | tests/rules/test_plan.py::test_ac2_emergency_fund_comes_first | planned |
| AC3 | ≤ 12-month money only liquid low-risk; nothing above risk score | automated | tests/rules/test_plan.py::test_ac3_expense_in_10_months_goes_to_liquid_low_risk; tests/rules/test_plan.py::test_ac3_risk_score_2_has_no_product_above_2 | planned |
| AC4 | Time machine replays 12 months, flags skipped months | automated | tests/rules/test_backtest.py::test_ac4_replays_twelve_months; tests/rules/test_backtest.py::test_ac4_month_breaking_minimum_is_flagged_skipped | planned |
| AC5 | Median surplus < 0 → no plan, customer told | automated | tests/rules/test_surplus.py::test_ac5_negative_median_gives_no_amount; tests/api/test_plans_api.py::test_ac5_no_surplus_creates_no_plan | planned |
| AC6 | < 3 months → ask expected savings; 3–5 months → low confidence, each transfer approved | automated | tests/rules/test_confidence.py::test_ac6_two_months_gives_no_estimate; tests/rules/test_confidence.py::test_ac6_four_months_is_low_confidence; tests/services/test_execution.py::test_ac6_low_confidence_transfer_waits_for_approval | planned |
| AC7 | Accept creates orders exactly once; reject creates none | automated | tests/services/test_acceptance.py::test_ac7_accepting_twice_creates_orders_once; tests/services/test_acceptance.py::test_ac7_rejected_plan_creates_no_orders; tests/services/test_execution.py::test_ac7_running_orders_twice_executes_once | planned |
| AC8 | Negative amount / past date → error; other customer's plan → 403 | automated | tests/api/test_plans_api.py::test_ac8_negative_amount_is_rejected; tests/api/test_plans_api.py::test_ac8_past_expense_date_is_rejected; tests/api/test_plans_api.py::test_ac8_other_customer_cannot_view_or_accept_plan | planned |
```

- [ ] **Step 4: Write ADR-0002**

`docs/decisions/0002-backend-rule-interpretations.md`:

```markdown
# 0002. Backend rule interpretations and M2 scope
Date: 2026-10-06 · Status: proposed

## Context
The specification fixes AC1–AC8 but leaves edge cases open. The rule engine must be deterministic,
so every open point needs one documented answer. AGENTS.md and docs/tasks.md also name modules that
no AC needs.

## Decision
1. Surplus months are complete calendar months before today. Months between the first data month
   and the last complete month that have no transactions count as 0 surplus. Own-account transfers
   and SaverAI savings transfers (`own_transfer = True`) are ignored.
2. All rounding rounds down to whole forints (`rules/money.py`). The median of an even count is the
   rounded-down mean of the two middle values.
3. AC5: a median surplus `<= 0` creates no plan (the spec says `< 0`; 0 gives a 0 HUF amount).
4. AC6: with fewer than 3 months the plan uses only the customer-entered expected monthly savings;
   its confidence is `none`, and like `low` every transfer needs explicit approval.
5. Low-risk means risk level `<= low_risk_max` (default 2) and never above the customer's risk score.
6. Allocation of the monthly amount, in priority order: emergency fund gets `min(amount, gap)` where
   gap = 3 × median monthly expenses − existing fund; planned expenses by due date get
   `ceil(expense / months left)` (at least 1 month); the remainder goes to long-term investment.
   The chosen product is the riskiest eligible one; ties go to the lowest id. No eligible product
   is an error shown to the customer.
7. Each repeated spec number is its own parameter: `min_months_for_estimate` and
   `emergency_fund_months` (3), `liquid_horizon_months` and `backtest_months` (12),
   `surplus_window_months` and `full_confidence_months` (6).
8. Time machine: principal only (no returns, no inflation). The transfer happens at month end after
   that month's transactions. A transfer that leaves exactly the minimum balance is allowed.
9. Mandate: signed on acceptance; version = customer's previous version + 1. Clauses: §1 listed
   products up to the monthly maximum, §2 minimum balance, §3 per-transfer approval, §4 pause.
10. Recurring orders are `plans.RecurringOrder` (not `banking.Order`), so `banking` never imports `plans`.
11. Orders run through `manage.py run_orders`; APScheduler is not added in M2.
12. Out of M2 scope: `rules/events.py`, `rules/tax.py`, `rules/whatif.py`, the inflation table,
    volatility in confidence.
13. The login endpoint is CSRF-exempt (Ninja default for unauthenticated operations);
    session-authenticated endpoints check CSRF.

## Alternatives considered
- Treat months without transactions as missing: hides months where the customer earned nothing.
- Round half up: could propose 1 HUF more than 70 %; rounding down never over-commits.
- Proportional split instead of strict priority: breaks AC2 ("before any investment").

## Consequences
- Every point above has a test; changing one means changing that test and this ADR (supersede it).
- The specification stays under 4,000 characters; these details live here.
```

- [ ] **Step 5: Add the Make target and changelog line**

In `Makefile`, change the `.PHONY` line and `check` target and add `docs-check`:

```make
.PHONY: setup migrate dev test lint fmt docs-check check

docs-check:
	python3 scripts/docs_check.py

check: lint test docs-check
```

Add to `CHANGELOG.md` under `### Added`:

```markdown
- `make docs-check`: AC ↔ traceability, referenced tests exist, changelog touched (AGENTS.md 8.6).
- ADR-0002 records rule interpretations for spec-silent edge cases and the M2 scope.
```

- [ ] **Step 6: Run it to verify it passes, then prove it catches errors**

Run: `make docs-check`
Expected: `docs-check: OK`.

Then temporarily change the AC1 row status from `planned` to `passing` and run `make docs-check`.
Expected: exit 1 with `docs-check: AC1: referenced test not found: tests/rules/test_surplus.py::test_ac1_median_surplus_gives_73500`. Change the status back to `planned`.

- [ ] **Step 7: Suggested commit (user commits)**

`docs: traceability table, docs-check script and ADR-0002`

---

### Task 3: Clock, money, months, defaults, rule types, purity guard

Deliverable: the pure foundations every rule module uses, plus a test that fails if `rules/` ever imports Django or reads the clock.

**Files:**
- Create: `backend/core/clock.py`, `backend/rules/__init__.py`, `backend/rules/money.py`, `backend/rules/months.py`, `backend/rules/defaults.py`, `backend/rules/types.py`
- Create: `backend/tests/conftest.py`, `backend/tests/constants.py`, `backend/tests/core/__init__.py`, `backend/tests/core/test_clock.py`, `backend/tests/rules/__init__.py`, `backend/tests/rules/test_money.py`, `backend/tests/rules/test_purity.py`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Produces:
  - `core.clock.Clock` (Protocol: `today() -> date`, `now() -> datetime`), `SystemClock`, `FixedClock.on(day: date) -> FixedClock`, `get_clock() -> Clock`
  - `rules.money`: `Huf = int`, `percent_of(amount: Huf, percent: int) -> Huf`, `median(values: Sequence[Huf]) -> Huf`, `ceil_div(amount: Huf, parts: int) -> Huf`
  - `rules.months`: `month_of(day: date) -> date`, `add_months(month: date, n: int) -> date`, `months_between(start: date, end: date) -> int`
  - `rules.defaults`: `RuleParams` (frozen dataclass, fields below), `DEFAULTS`
  - `rules.types`: `Txn(booked_on, amount, own_transfer=False, description="")`, `ProductInfo(id, name, risk_level, min_horizon_months, liquid)`, `PlannedExpense(name, amount, due_on)`
  - tests: `tests.constants.TODAY = date(2026, 10, 6)`, `LAST_MONTH = date(2026, 9, 1)`, `AC1_SERIES`; autouse fixture freezing `SAVERAI_FIXED_DATE` to `TODAY`; fixture `clock -> FixedClock`

- [ ] **Step 1: Write the failing tests**

`backend/tests/__init__.py` already exists. Create empty `backend/tests/core/__init__.py` and `backend/tests/rules/__init__.py`.

`backend/tests/constants.py`:

```python
"""Shared test constants. Pure: no Django imports."""

from datetime import date

TODAY = date(2026, 10, 6)  # mid-month on purpose: the current month is incomplete
LAST_MONTH = date(2026, 9, 1)  # last complete calendar month before TODAY
AC1_SERIES = [100_000, 120_000, 80_000, 110_000, 90_000, 300_000]  # oldest first
```

`backend/tests/conftest.py`:

```python
import pytest
from pytest_django.fixtures import SettingsWrapper

from core.clock import FixedClock
from tests.constants import TODAY


@pytest.fixture(autouse=True)
def fixed_today(settings: SettingsWrapper) -> None:
    """Every test runs on TODAY, also code that calls core.clock.get_clock()."""
    settings.SAVERAI_FIXED_DATE = TODAY.isoformat()


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock.on(TODAY)
```

`backend/tests/core/test_clock.py`:

```python
from datetime import date

from pytest_django.fixtures import SettingsWrapper

from core.clock import FixedClock, SystemClock, get_clock


def test_fixed_clock_returns_its_day() -> None:
    clock = FixedClock.on(date(2026, 10, 6))
    assert clock.today() == date(2026, 10, 6)
    assert clock.now().date() == date(2026, 10, 6)


def test_get_clock_uses_fixed_date_setting(settings: SettingsWrapper) -> None:
    settings.SAVERAI_FIXED_DATE = "2026-01-31"
    assert get_clock().today() == date(2026, 1, 31)


def test_get_clock_without_setting_is_system_clock(settings: SettingsWrapper) -> None:
    settings.SAVERAI_FIXED_DATE = None
    assert isinstance(get_clock(), SystemClock)
```

`backend/tests/rules/test_money.py`:

```python
from datetime import date

import pytest

from rules.defaults import DEFAULTS
from rules.money import ceil_div, median, percent_of
from rules.months import add_months, month_of, months_between


def test_percent_of_rounds_down_to_whole_forint() -> None:
    assert percent_of(105_000, 70) == 73_500
    assert percent_of(10_001, 70) == 7_000  # 7000.7 → 7000


def test_median_odd_and_even_counts() -> None:
    assert median([3, 1, 2]) == 2
    assert median([110_000, 100_000]) == 105_000
    assert median([10_002, 10_003]) == 10_002  # 10002.5 rounds down
    assert median([-1, 0]) == -1  # rounds down, also below zero


def test_median_of_empty_sequence_raises() -> None:
    with pytest.raises(ValueError):
        median([])


def test_ceil_div_rounds_up() -> None:
    assert ceil_div(500_000, 10) == 50_000
    assert ceil_div(100, 3) == 34


def test_month_helpers() -> None:
    assert month_of(date(2026, 10, 6)) == date(2026, 10, 1)
    assert add_months(date(2026, 11, 1), 2) == date(2027, 1, 1)
    assert add_months(date(2026, 1, 1), -1) == date(2025, 12, 1)
    assert months_between(date(2026, 10, 1), date(2027, 8, 1)) == 10


def test_defaults_match_specification() -> None:
    assert DEFAULTS.monthly_share_percent == 70
    assert DEFAULTS.surplus_window_months == 6
    assert DEFAULTS.min_months_for_estimate == 3
    assert DEFAULTS.full_confidence_months == 6
    assert DEFAULTS.emergency_fund_months == 3
    assert DEFAULTS.liquid_horizon_months == 12
    assert DEFAULTS.min_balance == 100_000
    assert DEFAULTS.backtest_months == 12
```

`backend/tests/rules/test_purity.py`:

```python
"""Golden rule 4: rules/ must not import Django, the DB, the network or read the system clock."""

import ast
from pathlib import Path

RULES = Path(__file__).resolve().parents[2] / "rules"
FORBIDDEN_MODULES = {"django", "core", "banking", "plans", "api", "socket", "urllib", "http"}
CLOCK_CALLS = {"now", "today", "utcnow"}


def imported_modules(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    return names


def clock_calls(tree: ast.AST) -> list[str]:
    calls = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in CLOCK_CALLS
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in {"date", "datetime", "timezone"}
        ):
            calls.append(f"{node.func.value.id}.{node.func.attr}()")
    return calls


def test_rules_package_is_pure() -> None:
    files = sorted(RULES.glob("*.py"))
    assert files, "rules/ has no modules"
    for file in files:
        tree = ast.parse(file.read_text())
        for module in imported_modules(tree):
            assert module.split(".")[0] not in FORBIDDEN_MODULES, f"{file.name} imports {module}"
        assert clock_calls(tree) == [], f"{file.name} reads the system clock"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/core tests/rules`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.clock'` / `'rules'`.

- [ ] **Step 3: Implement**

`backend/core/clock.py`:

```python
"""Injected time source (AGENTS.md golden rule 5). The only module that reads the system clock."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from typing import Protocol

from django.conf import settings
from django.utils import timezone


class Clock(Protocol):
    def today(self) -> date: ...

    def now(self) -> datetime: ...


class SystemClock:
    def today(self) -> date:
        return timezone.localdate()

    def now(self) -> datetime:
        return timezone.now()


@dataclass(frozen=True)
class FixedClock:
    moment: datetime

    @classmethod
    def on(cls, day: date) -> "FixedClock":
        return cls(datetime.combine(day, time(12), tzinfo=UTC))

    def today(self) -> date:
        return self.moment.date()

    def now(self) -> datetime:
        return self.moment


def get_clock() -> Clock:
    """FixedClock when settings.SAVERAI_FIXED_DATE is set (demos, tests), otherwise SystemClock."""
    fixed = settings.SAVERAI_FIXED_DATE
    return FixedClock.on(date.fromisoformat(fixed)) if fixed else SystemClock()
```

`backend/rules/__init__.py`:

```python
"""Pure rule engine: plain data in, results out. No Django, database, network or system clock."""
```

`backend/rules/money.py`:

```python
"""Money type and the only rounding rules (AGENTS.md golden rule 3). Everything rounds down
to whole forints, except ceil_div, which is used where a target must be reached in time."""

from collections.abc import Sequence

Huf = int


def percent_of(amount: Huf, percent: int) -> Huf:
    """`percent` % of `amount`, rounded down."""
    return amount * percent // 100


def median(values: Sequence[Huf]) -> Huf:
    """Median; for an even count, the mean of the two middle values rounded down."""
    if not values:
        raise ValueError("median of an empty sequence")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) // 2


def ceil_div(amount: Huf, parts: int) -> Huf:
    """`amount` split into `parts`, rounded up, so that `parts` payments reach `amount`."""
    return -(-amount // parts)
```

`backend/rules/months.py`:

```python
"""Calendar-month arithmetic. A month is represented by its first day."""

from datetime import date


def month_of(day: date) -> date:
    return day.replace(day=1)


def add_months(month: date, n: int) -> date:
    index = month.year * 12 + month.month - 1 + n
    return date(index // 12, index % 12 + 1, 1)


def months_between(start: date, end: date) -> int:
    """Whole calendar months from start's month to end's month (Oct → Aug next year = 10)."""
    return (end.year - start.year) * 12 + end.month - start.month
```

`backend/rules/defaults.py`:

```python
"""Default rule parameters (spec "Plan rules"). Runtime values come from plans.models.RuleConfig,
which is editable in Django admin and uses these as defaults."""

from dataclasses import dataclass

from rules.money import Huf


@dataclass(frozen=True)
class RuleParams:
    monthly_share_percent: int = 70  # AC1: share of the median surplus
    surplus_window_months: int = 6  # AC1: months in the median
    min_months_for_estimate: int = 3  # AC6: fewer → no estimate
    full_confidence_months: int = 6  # AC6: fewer → low confidence
    emergency_fund_months: int = 3  # AC2: emergency fund = N × median monthly expenses
    liquid_horizon_months: int = 12  # AC3: needed within N months → liquid low-risk only
    low_risk_max: int = 2  # AC3: "low-risk" = risk level ≤ this (ADR-0002)
    min_balance: Huf = 100_000  # AC4: never transfer below this balance
    backtest_months: int = 12  # AC4: months replayed by the time machine


DEFAULTS = RuleParams()
```

`backend/rules/types.py`:

```python
"""Plain input types of the rule engine."""

from dataclasses import dataclass
from datetime import date

from rules.money import Huf


@dataclass(frozen=True)
class Txn:
    booked_on: date
    amount: Huf  # positive: income, negative: expense
    own_transfer: bool = False  # between own accounts or a SaverAI savings transfer
    description: str = ""


@dataclass(frozen=True)
class ProductInfo:
    id: int
    name: str
    risk_level: int  # 1 (lowest) … 5
    min_horizon_months: int
    liquid: bool


@dataclass(frozen=True)
class PlannedExpense:
    name: str
    amount: Huf
    due_on: date
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/core tests/rules -v`
Expected: all pass (3 clock, 6 money, 1 purity).

- [ ] **Step 5: Lint, docs, check**

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Injected `Clock` (`core/clock.py`), integer-forint money helpers, calendar-month helpers and default rule parameters (`rules/defaults.py`).
- Purity test: `rules/` may not import Django or read the system clock (golden rule 4).
```

Run: `make fmt && make check`
Expected: green.

- [ ] **Step 6: Suggested commit (user commits)**

`feat(rules): clock, money, months and default rule parameters`

---

### Task 4: Monthly surplus and suggested amount (AC1, AC5) + synthetic data generator

Deliverable: `analyse_surplus()` turns raw transactions into monthly flows, the median surplus and the suggested monthly amount. `banking/synthetic.py` builds deterministic transaction series for tests and `make seed`.

**Files:**
- Create: `backend/rules/surplus.py`, `backend/banking/synthetic.py`, `backend/tests/rules/test_surplus.py`
- Modify: `docs/traceability.md` (AC1 row → `passing`), `CHANGELOG.md`

**Interfaces:**
- Consumes: `Txn`, `RuleParams`/`DEFAULTS`, `median`, `percent_of`, `month_of`, `add_months`, `months_between` (Task 3)
- Produces:
  - `rules.surplus.MonthFlow(month: date, income: Huf, expenses: Huf)` with property `surplus`
  - `rules.surplus.SurplusAnalysis(months_of_data: int, flows: tuple[MonthFlow, ...], median_surplus: Huf | None, median_expenses: Huf, monthly_amount: Huf | None)` — `monthly_amount is None` → too little data (AC6); `== 0` → no surplus (AC5)
  - `rules.surplus.analyse_surplus(transactions: Sequence[Txn], today: date, params: RuleParams = DEFAULTS) -> SurplusAnalysis`
  - `banking.synthetic.monthly_series(last_month: date, surpluses: Sequence[Huf], *, expenses: Huf = 250_000) -> list[Txn]` — per month: rent −60 % of expenses (day 3), salary = expenses + surplus (day 10), bills −40 % (day 20), own-account transfer −30,000 (day 25, `own_transfer=True`)

- [ ] **Step 1: Write the failing tests**

`backend/tests/rules/test_surplus.py`:

```python
from datetime import date

import pytest

from banking.synthetic import monthly_series
from rules.surplus import MonthFlow, analyse_surplus
from rules.types import Txn
from tests.constants import AC1_SERIES, LAST_MONTH, TODAY


def test_ac1_median_surplus_gives_73500() -> None:
    result = analyse_surplus(monthly_series(LAST_MONTH, AC1_SERIES), TODAY)
    assert [flow.surplus for flow in result.flows] == AC1_SERIES
    assert result.median_surplus == 105_000
    assert result.monthly_amount == 73_500


def test_ac1_own_account_transfers_are_ignored() -> None:
    txns = monthly_series(LAST_MONTH, AC1_SERIES)
    txns.append(Txn(date(2026, 9, 15), -500_000, own_transfer=True))
    assert analyse_surplus(txns, TODAY).monthly_amount == 73_500


def test_ac1_current_partial_month_is_ignored() -> None:
    txns = monthly_series(LAST_MONTH, AC1_SERIES)
    txns.append(Txn(date(2026, 10, 2), 1_000_000))
    result = analyse_surplus(txns, TODAY)
    assert result.monthly_amount == 73_500
    assert result.flows[-1].month == LAST_MONTH


def test_ac1_only_last_six_months_count() -> None:
    txns = monthly_series(LAST_MONTH, [5_000_000, 5_000_000, *AC1_SERIES])
    result = analyse_surplus(txns, TODAY)
    assert result.months_of_data == 8
    assert result.monthly_amount == 73_500


def test_month_without_transactions_counts_as_zero_surplus() -> None:
    # March–May and July–September have data, June has none.
    txns = monthly_series(date(2026, 5, 1), [100_000] * 3) + monthly_series(
        LAST_MONTH, [100_000] * 3
    )
    result = analyse_surplus(txns, TODAY)
    assert result.months_of_data == 7
    assert result.flows[2] == MonthFlow(date(2026, 6, 1), income=0, expenses=0)
    assert result.median_surplus == 100_000


def test_even_median_rounds_down() -> None:
    result = analyse_surplus(monthly_series(LAST_MONTH, [10_001, 10_002, 10_003, 10_004]), TODAY)
    assert result.median_surplus == 10_002
    assert result.monthly_amount == 7_001


def test_ac5_negative_median_gives_no_amount() -> None:
    result = analyse_surplus(monthly_series(LAST_MONTH, [-50_000] * 6), TODAY)
    assert result.median_surplus == -50_000
    assert result.monthly_amount == 0


def test_ac5_zero_median_gives_no_amount() -> None:
    # ADR-0002: a median of exactly 0 also means no surplus.
    result = analyse_surplus(monthly_series(LAST_MONTH, [0] * 6), TODAY)
    assert result.monthly_amount == 0


def test_too_little_data_gives_no_estimate_but_keeps_expenses() -> None:
    result = analyse_surplus(monthly_series(LAST_MONTH, [60_000, 70_000]), TODAY)
    assert result.months_of_data == 2
    assert result.median_surplus is None
    assert result.monthly_amount is None
    assert result.median_expenses == 250_000


def test_no_transactions_at_all() -> None:
    result = analyse_surplus([], TODAY)
    assert result.months_of_data == 0
    assert result.flows == ()
    assert result.median_expenses == 0
    assert result.monthly_amount is None


def test_synthetic_series_rejects_impossible_surplus() -> None:
    with pytest.raises(ValueError):
        monthly_series(LAST_MONTH, [-300_000])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/rules/test_surplus.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'banking.synthetic'`.

- [ ] **Step 3: Implement**

`backend/banking/synthetic.py`:

```python
"""Deterministic synthetic transactions for `make seed` and tests. Pure: no Django, no clock."""

from collections.abc import Sequence
from datetime import date

from rules.money import Huf
from rules.months import add_months
from rules.types import Txn

DEFAULT_EXPENSES: Huf = 250_000
OWN_TRANSFER: Huf = 30_000


def monthly_series(
    last_month: date, surpluses: Sequence[Huf], *, expenses: Huf = DEFAULT_EXPENSES
) -> list[Txn]:
    """One month of transactions per surplus value, oldest first, ending with `last_month`.

    Each month: rent (60 % of expenses), salary (expenses + surplus), bills (the rest of the
    expenses) and an own-account transfer, which the surplus calculation must ignore.
    """
    first = add_months(last_month, -(len(surpluses) - 1))
    rent = expenses * 6 // 10
    txns: list[Txn] = []
    for index, surplus in enumerate(surpluses):
        income = expenses + surplus
        if income < 0:
            raise ValueError(f"surplus {surplus} is below -expenses ({-expenses})")
        month = add_months(first, index)
        txns += [
            Txn(month.replace(day=3), -rent, description="Rent"),
            Txn(month.replace(day=10), income, description="Salary"),
            Txn(month.replace(day=20), -(expenses - rent), description="Groceries and bills"),
            Txn(
                month.replace(day=25),
                -OWN_TRANSFER,
                own_transfer=True,
                description="To own savings account",
            ),
        ]
    return txns
```

`backend/rules/surplus.py`:

```python
"""Monthly surplus and suggested monthly amount (AC1, AC5; AC6 "no estimate")."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from rules.defaults import DEFAULTS, RuleParams
from rules.money import Huf, median, percent_of
from rules.months import add_months, month_of, months_between
from rules.types import Txn


@dataclass(frozen=True)
class MonthFlow:
    month: date  # first day of the calendar month
    income: Huf
    expenses: Huf  # positive number

    @property
    def surplus(self) -> Huf:
        return self.income - self.expenses


@dataclass(frozen=True)
class SurplusAnalysis:
    months_of_data: int
    flows: tuple[MonthFlow, ...]  # the analysed window, oldest first
    median_surplus: Huf | None  # None: too little data for an estimate (AC6)
    median_expenses: Huf  # 0 when there is no data
    monthly_amount: Huf | None  # None: no estimate (AC6); 0: no surplus (AC5)


def complete_months(transactions: Sequence[Txn], today: date) -> list[date]:
    """Calendar months from the first counted transaction up to the month before `today`."""
    current = month_of(today)
    booked = [
        month_of(t.booked_on)
        for t in transactions
        if not t.own_transfer and month_of(t.booked_on) < current
    ]
    if not booked:
        return []
    first = min(booked)
    return [add_months(first, i) for i in range(months_between(first, current))]


def month_flows(transactions: Sequence[Txn], months: Sequence[date]) -> tuple[MonthFlow, ...]:
    income = dict.fromkeys(months, 0)
    expenses = dict.fromkeys(months, 0)
    for t in transactions:
        month = month_of(t.booked_on)
        if t.own_transfer or month not in income:
            continue
        if t.amount >= 0:
            income[month] += t.amount
        else:
            expenses[month] -= t.amount
    return tuple(MonthFlow(m, income[m], expenses[m]) for m in months)


def analyse_surplus(
    transactions: Sequence[Txn], today: date, params: RuleParams = DEFAULTS
) -> SurplusAnalysis:
    """Median surplus of the last complete months and the suggested monthly amount.

    Inputs: the customer's transactions, today's date (from the Clock), rule parameters.
    Output: monthly_amount = monthly_share_percent % of the median surplus of the last
    surplus_window_months complete months (AC1); 0 if that median is not positive (AC5);
    None if fewer than min_months_for_estimate months exist (AC6).
    """
    months = complete_months(transactions, today)
    flows = month_flows(transactions, months[-params.surplus_window_months :])
    median_expenses = median([f.expenses for f in flows]) if flows else 0
    if len(months) < params.min_months_for_estimate:
        return SurplusAnalysis(len(months), flows, None, median_expenses, None)
    median_surplus = median([f.surplus for f in flows])
    amount = percent_of(median_surplus, params.monthly_share_percent) if median_surplus > 0 else 0
    return SurplusAnalysis(len(months), flows, median_surplus, median_expenses, amount)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/rules/test_surplus.py -v`
Expected: 11 passed.

- [ ] **Step 5: Docs and check**

In `docs/traceability.md` set the AC1 row status to `passing`. (AC5 stays `planned` until its API test exists in Task 13.)

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Monthly surplus analysis: median of the last 6 complete months, 70 % suggested amount, no amount without surplus (AC1, AC5, ADR-0002).
- Deterministic synthetic transaction generator (`banking/synthetic.py`).
```

Run: `make fmt && make check`
Expected: green; docs-check OK.

- [ ] **Step 6: Suggested commit (user commits)**

`feat(rules): median monthly surplus and suggested amount (AC1, AC5)`

---

### Task 5: Confidence level (AC6)

Deliverable: confidence from the number of data months, and the rule that non-normal confidence needs per-transfer approval.

**Files:**
- Create: `backend/rules/confidence.py`, `backend/tests/rules/test_confidence.py`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `RuleParams`, `analyse_surplus` (Task 4)
- Produces: `rules.confidence.Confidence` (`StrEnum`: `NONE = "none"`, `LOW = "low"`, `NORMAL = "normal"`), `assess_confidence(months_of_data: int, params: RuleParams = DEFAULTS) -> Confidence`, `needs_per_transfer_approval(confidence: Confidence) -> bool`

- [ ] **Step 1: Write the failing tests**

`backend/tests/rules/test_confidence.py`:

```python
import pytest

from banking.synthetic import monthly_series
from rules.confidence import Confidence, assess_confidence, needs_per_transfer_approval
from rules.surplus import analyse_surplus
from tests.constants import LAST_MONTH, TODAY


def test_ac6_two_months_gives_no_estimate() -> None:
    analysis = analyse_surplus(monthly_series(LAST_MONTH, [60_000, 70_000]), TODAY)
    assert analysis.monthly_amount is None
    assert assess_confidence(analysis.months_of_data) is Confidence.NONE


def test_ac6_four_months_is_low_confidence() -> None:
    analysis = analyse_surplus(monthly_series(LAST_MONTH, [50_000, 60_000, 55_000, 65_000]), TODAY)
    confidence = assess_confidence(analysis.months_of_data)
    assert analysis.monthly_amount == 40_250
    assert confidence is Confidence.LOW
    assert needs_per_transfer_approval(confidence)


@pytest.mark.parametrize(
    ("months", "expected"),
    [
        (0, Confidence.NONE),
        (2, Confidence.NONE),
        (3, Confidence.LOW),
        (5, Confidence.LOW),
        (6, Confidence.NORMAL),
        (12, Confidence.NORMAL),
    ],
)
def test_confidence_boundaries(months: int, expected: Confidence) -> None:
    assert assess_confidence(months) is expected


def test_only_normal_confidence_skips_per_transfer_approval() -> None:
    assert not needs_per_transfer_approval(Confidence.NORMAL)
    assert needs_per_transfer_approval(Confidence.NONE)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/rules/test_confidence.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'rules.confidence'`.

- [ ] **Step 3: Implement**

`backend/rules/confidence.py`:

```python
"""Confidence level from the amount of transaction data (AC6)."""

from enum import StrEnum

from rules.defaults import DEFAULTS, RuleParams


class Confidence(StrEnum):
    NONE = "none"  # too little data: no estimate, customer enters expected savings
    LOW = "low"
    NORMAL = "normal"


def assess_confidence(months_of_data: int, params: RuleParams = DEFAULTS) -> Confidence:
    """AC6: < min_months_for_estimate → NONE; < full_confidence_months → LOW; else NORMAL."""
    if months_of_data < params.min_months_for_estimate:
        return Confidence.NONE
    if months_of_data < params.full_confidence_months:
        return Confidence.LOW
    return Confidence.NORMAL


def needs_per_transfer_approval(confidence: Confidence) -> bool:
    """AC6: every transfer of a plan without normal confidence needs explicit approval."""
    return confidence is not Confidence.NORMAL
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/rules/test_confidence.py -v`
Expected: 9 passed.

- [ ] **Step 5: Docs and check**

AC6 row stays `planned` (its execution-level test comes in Task 12). Add to `CHANGELOG.md` under `### Added`:

```markdown
- Confidence level: no estimate under 3 months, low confidence for 3–5 months (AC6).
```

Run: `make fmt && make check`. Expected: green.

- [ ] **Step 6: Suggested commit (user commits)**

`feat(rules): confidence level from months of data (AC6)`

---

### Task 6: Plan allocation and product filtering (AC2, AC3, AC5, AC6)

Deliverable: `allocate()` splits a monthly amount by priority with risk/liquidity/horizon filters; `propose()` runs the whole rule chain and returns `plan`, `no_surplus` or `needs_expected_savings`.

**Files:**
- Create: `backend/rules/plan.py`, `backend/tests/rules/test_plan.py`
- Modify: `docs/traceability.md` (AC2, AC3 → `passing`), `CHANGELOG.md`

**Interfaces:**
- Consumes: `analyse_surplus`, `SurplusAnalysis` (Task 4); `Confidence`, `assess_confidence` (Task 5); `ProductInfo`, `PlannedExpense`, `Txn`, `ceil_div`, `months_between`, `month_of` (Task 3)
- Produces:
  - `rules.plan.ItemKind` (`StrEnum`: `EMERGENCY_FUND = "emergency_fund"`, `PLANNED_EXPENSE = "planned_expense"`, `INVESTMENT = "investment"`)
  - `rules.plan.Outcome` (`StrEnum`: `PLAN = "plan"`, `NO_SURPLUS = "no_surplus"`, `NEEDS_EXPECTED_SAVINGS = "needs_expected_savings"`)
  - `rules.plan.NoEligibleProduct(Exception)`
  - `rules.plan.PlanItemDraft(kind: ItemKind, label: str, product: ProductInfo, monthly_amount: Huf, target_amount: Huf | None, horizon_months: int | None)`
  - `rules.plan.PlanInputs(today: date, risk_score: int, existing_emergency_fund: Huf, expected_monthly_savings: Huf | None, planned_expenses: Sequence[PlannedExpense], transactions: Sequence[Txn])`
  - `rules.plan.Proposal(outcome: Outcome, analysis: SurplusAnalysis, confidence: Confidence, monthly_amount: Huf, items: tuple[PlanItemDraft, ...])`
  - `rules.plan.allocate(monthly_amount: Huf, *, median_expenses: Huf, risk_score: int, existing_emergency_fund: Huf, planned_expenses: Sequence[PlannedExpense], today: date, products: Sequence[ProductInfo], params: RuleParams = DEFAULTS) -> tuple[PlanItemDraft, ...]`
  - `rules.plan.propose(inputs: PlanInputs, products: Sequence[ProductInfo], params: RuleParams = DEFAULTS) -> Proposal`

- [ ] **Step 1: Write the failing tests**

`backend/tests/rules/test_plan.py`:

```python
from collections.abc import Sequence
from datetime import date

import pytest

from banking.synthetic import monthly_series
from rules.confidence import Confidence
from rules.money import Huf
from rules.plan import (
    ItemKind,
    NoEligibleProduct,
    Outcome,
    PlanInputs,
    PlanItemDraft,
    allocate,
    propose,
)
from rules.types import PlannedExpense, ProductInfo
from tests.constants import AC1_SERIES, LAST_MONTH, TODAY

MONEY_MARKET = ProductInfo(1, "Money market fund", 1, 0, True)
SHORT_BOND = ProductInfo(2, "Short government bond fund", 2, 0, True)
BALANCED = ProductInfo(3, "Balanced fund", 3, 36, False)
EQUITY = ProductInfo(4, "Global equity fund", 5, 60, False)
CATALOGUE = (MONEY_MARKET, SHORT_BOND, BALANCED, EQUITY)
FULL_FUND = 750_000  # 3 × 250,000 median expenses


def plan_for(
    amount: Huf,
    *,
    risk: int = 5,
    fund: Huf = FULL_FUND,
    expenses: Sequence[PlannedExpense] = (),
    median_expenses: Huf = 250_000,
    products: Sequence[ProductInfo] = CATALOGUE,
) -> tuple[PlanItemDraft, ...]:
    return allocate(
        amount,
        median_expenses=median_expenses,
        risk_score=risk,
        existing_emergency_fund=fund,
        planned_expenses=expenses,
        today=TODAY,
        products=products,
    )


def summary(items: Sequence[PlanItemDraft]) -> list[tuple[ItemKind, Huf]]:
    return [(item.kind, item.monthly_amount) for item in items]


def test_ac2_emergency_fund_comes_first() -> None:
    items = plan_for(73_500, fund=0)
    assert summary(items) == [(ItemKind.EMERGENCY_FUND, 73_500)]
    assert items[0].target_amount == 750_000
    assert items[0].product.liquid


def test_ac2_investment_gets_only_what_is_left() -> None:
    items = plan_for(73_500, fund=700_000)
    assert summary(items) == [(ItemKind.EMERGENCY_FUND, 50_000), (ItemKind.INVESTMENT, 23_500)]
    assert items[1].product == EQUITY


def test_full_emergency_fund_skips_emergency_item() -> None:
    assert summary(plan_for(73_500)) == [(ItemKind.INVESTMENT, 73_500)]


def test_ac3_expense_in_10_months_goes_to_liquid_low_risk() -> None:
    car = PlannedExpense("Car", 500_000, date(2027, 8, 15))  # October 2026 → August 2027
    items = plan_for(73_500, expenses=[car])
    assert summary(items) == [(ItemKind.PLANNED_EXPENSE, 50_000), (ItemKind.INVESTMENT, 23_500)]
    assert items[0].horizon_months == 10
    assert items[0].product.liquid
    assert items[0].product.risk_level <= 2


def test_ac3_risk_score_2_has_no_product_above_2() -> None:
    renovation = PlannedExpense("Renovation", 240_000, date(2028, 10, 1))  # 24 months
    items = plan_for(300_000, risk=2, fund=0, median_expenses=50_000, expenses=[renovation])
    assert summary(items) == [
        (ItemKind.EMERGENCY_FUND, 150_000),
        (ItemKind.PLANNED_EXPENSE, 10_000),
        (ItemKind.INVESTMENT, 140_000),
    ]
    assert max(item.product.risk_level for item in items) <= 2


def test_twelve_months_is_short_term_and_thirteen_is_not() -> None:
    one_year_bond = ProductInfo(5, "One-year corporate bond", 3, 12, False)
    catalogue = (*CATALOGUE, one_year_bond)
    in_12 = plan_for(73_500, expenses=[PlannedExpense("Trip", 120_000, date(2027, 10, 1))],
                     products=catalogue)
    in_13 = plan_for(73_500, expenses=[PlannedExpense("Trip", 130_000, date(2027, 11, 1))],
                     products=catalogue)
    assert in_12[0].product == SHORT_BOND
    assert in_13[0].product == one_year_bond


def test_expense_due_this_month_needs_full_amount_now() -> None:
    insurance = PlannedExpense("Insurance", 60_000, date(2026, 10, 20))
    items = plan_for(73_500, expenses=[insurance])
    assert summary(items) == [(ItemKind.PLANNED_EXPENSE, 60_000), (ItemKind.INVESTMENT, 13_500)]
    assert items[0].horizon_months == 1


def test_planned_expenses_are_ordered_by_due_date() -> None:
    later = PlannedExpense("Later", 100_000, date(2027, 9, 1))
    sooner = PlannedExpense("Sooner", 100_000, date(2027, 1, 1))
    items = plan_for(73_500, expenses=[later, sooner])
    assert [item.label for item in items[:2]] == ["Sooner", "Later"]


def test_no_eligible_product_raises() -> None:
    with pytest.raises(NoEligibleProduct):
        plan_for(73_500, fund=0, products=(EQUITY,))


def inputs(surpluses: list[Huf], *, expected: Huf | None = None) -> PlanInputs:
    return PlanInputs(
        today=TODAY,
        risk_score=5,
        existing_emergency_fund=FULL_FUND,
        expected_monthly_savings=expected,
        planned_expenses=(),
        transactions=monthly_series(LAST_MONTH, surpluses),
    )


def test_ac1_proposal_uses_73500() -> None:
    proposal = propose(inputs(AC1_SERIES), CATALOGUE)
    assert proposal.outcome is Outcome.PLAN
    assert proposal.monthly_amount == 73_500
    assert proposal.confidence is Confidence.NORMAL
    assert summary(proposal.items) == [(ItemKind.INVESTMENT, 73_500)]


def test_ac5_no_surplus_gives_no_plan() -> None:
    proposal = propose(inputs([-50_000] * 6), CATALOGUE)
    assert proposal.outcome is Outcome.NO_SURPLUS
    assert proposal.items == ()


def test_ac6_too_little_data_asks_for_expected_savings() -> None:
    proposal = propose(inputs([60_000, 70_000]), CATALOGUE)
    assert proposal.outcome is Outcome.NEEDS_EXPECTED_SAVINGS
    assert proposal.items == ()


def test_ac6_expected_savings_are_used_when_data_is_short() -> None:
    proposal = propose(inputs([60_000, 70_000], expected=40_000), CATALOGUE)
    assert proposal.outcome is Outcome.PLAN
    assert proposal.monthly_amount == 40_000
    assert proposal.confidence is Confidence.NONE


def test_ac6_four_months_gives_low_confidence_plan() -> None:
    proposal = propose(inputs([50_000, 60_000, 55_000, 65_000]), CATALOGUE)
    assert proposal.outcome is Outcome.PLAN
    assert proposal.confidence is Confidence.LOW
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/rules/test_plan.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'rules.plan'`.

- [ ] **Step 3: Implement**

`backend/rules/plan.py`:

```python
"""Plan proposal: priority allocation and product filtering (AC2, AC3, AC5, AC6).

Priority (spec "Plan rules"): emergency fund → planned expenses (by due date) → long-term
investment. Money needed within liquid_horizon_months goes only to liquid low-risk products.
No product above the customer's risk score is ever chosen. Details: ADR-0002.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from rules.confidence import Confidence, assess_confidence
from rules.defaults import DEFAULTS, RuleParams
from rules.money import Huf, ceil_div
from rules.months import month_of, months_between
from rules.surplus import SurplusAnalysis, analyse_surplus
from rules.types import PlannedExpense, ProductInfo, Txn


class ItemKind(StrEnum):
    EMERGENCY_FUND = "emergency_fund"
    PLANNED_EXPENSE = "planned_expense"
    INVESTMENT = "investment"


class Outcome(StrEnum):
    PLAN = "plan"
    NO_SURPLUS = "no_surplus"  # AC5
    NEEDS_EXPECTED_SAVINGS = "needs_expected_savings"  # AC6


class NoEligibleProduct(Exception):
    """No active product satisfies the risk, liquidity and horizon limits."""


@dataclass(frozen=True)
class PlanItemDraft:
    kind: ItemKind
    label: str
    product: ProductInfo
    monthly_amount: Huf
    target_amount: Huf | None
    horizon_months: int | None


@dataclass(frozen=True)
class PlanInputs:
    today: date
    risk_score: int  # 1–5 from the questionnaire
    existing_emergency_fund: Huf
    expected_monthly_savings: Huf | None  # asked when data is too short (AC6)
    planned_expenses: Sequence[PlannedExpense]
    transactions: Sequence[Txn]


@dataclass(frozen=True)
class Proposal:
    outcome: Outcome
    analysis: SurplusAnalysis
    confidence: Confidence
    monthly_amount: Huf
    items: tuple[PlanItemDraft, ...]


def pick_product(
    products: Sequence[ProductInfo],
    *,
    max_risk: int,
    liquid_only: bool,
    horizon_months: int | None,
) -> ProductInfo:
    """Riskiest product within the limits; ties go to the lowest id. Raises NoEligibleProduct."""
    eligible = [
        p
        for p in products
        if p.risk_level <= max_risk
        and (p.liquid or not liquid_only)
        and (horizon_months is None or p.min_horizon_months <= horizon_months)
    ]
    if not eligible:
        liquid = " liquid" if liquid_only else ""
        raise NoEligibleProduct(
            f"No{liquid} product with risk level ≤ {max_risk} is available. "
            "Please contact the bank."
        )
    return max(eligible, key=lambda p: (p.risk_level, -p.id))


def allocate(
    monthly_amount: Huf,
    *,
    median_expenses: Huf,
    risk_score: int,
    existing_emergency_fund: Huf,
    planned_expenses: Sequence[PlannedExpense],
    today: date,
    products: Sequence[ProductInfo],
    params: RuleParams = DEFAULTS,
) -> tuple[PlanItemDraft, ...]:
    """Split `monthly_amount` by priority (AC2) with risk and liquidity filters (AC3)."""
    low_risk_cap = min(risk_score, params.low_risk_max)
    remaining = monthly_amount
    items: list[PlanItemDraft] = []

    target = params.emergency_fund_months * median_expenses
    gap = max(0, target - existing_emergency_fund)
    if gap > 0:
        product = pick_product(products, max_risk=low_risk_cap, liquid_only=True, horizon_months=0)
        amount = min(remaining, gap)
        items.append(
            PlanItemDraft(ItemKind.EMERGENCY_FUND, "Emergency fund", product, amount, target, None)
        )
        remaining -= amount

    for expense in sorted(planned_expenses, key=lambda e: (e.due_on, e.name)):
        if remaining == 0:
            break
        horizon = max(1, months_between(month_of(today), month_of(expense.due_on)))
        short_term = horizon <= params.liquid_horizon_months
        product = pick_product(
            products,
            max_risk=low_risk_cap if short_term else risk_score,
            liquid_only=short_term,
            horizon_months=horizon,
        )
        amount = min(remaining, ceil_div(expense.amount, horizon))
        items.append(
            PlanItemDraft(
                ItemKind.PLANNED_EXPENSE, expense.name, product, amount, expense.amount, horizon
            )
        )
        remaining -= amount

    if remaining > 0:
        product = pick_product(products, max_risk=risk_score, liquid_only=False, horizon_months=None)
        items.append(
            PlanItemDraft(ItemKind.INVESTMENT, "Long-term investment", product, remaining, None, None)
        )
    return tuple(items)


def propose(
    inputs: PlanInputs, products: Sequence[ProductInfo], params: RuleParams = DEFAULTS
) -> Proposal:
    """Full rule chain: surplus (AC1) → confidence (AC6) → outcome (AC5, AC6) → allocation."""
    analysis = analyse_surplus(inputs.transactions, inputs.today, params)
    confidence = assess_confidence(analysis.months_of_data, params)
    if analysis.monthly_amount is None:
        if inputs.expected_monthly_savings is None:
            return Proposal(Outcome.NEEDS_EXPECTED_SAVINGS, analysis, confidence, 0, ())
        amount = inputs.expected_monthly_savings
    else:
        amount = analysis.monthly_amount
    if amount <= 0:
        return Proposal(Outcome.NO_SURPLUS, analysis, confidence, 0, ())
    items = allocate(
        amount,
        median_expenses=analysis.median_expenses,
        risk_score=inputs.risk_score,
        existing_emergency_fund=inputs.existing_emergency_fund,
        planned_expenses=inputs.planned_expenses,
        today=inputs.today,
        products=products,
        params=params,
    )
    return Proposal(Outcome.PLAN, analysis, confidence, amount, items)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/rules/test_plan.py -v`
Expected: 14 passed.

- [ ] **Step 5: Docs and check**

In `docs/traceability.md` set AC2 and AC3 to `passing`. Add to `CHANGELOG.md` under `### Added`:

```markdown
- Plan allocation: emergency fund → planned expenses → investment; ≤ 12-month money only in liquid low-risk products; no product above the customer's risk score (AC2, AC3, ADR-0002).
- Plan proposal outcomes: plan, no surplus (AC5), expected savings needed (AC6).
```

Run: `make fmt && make check`. Expected: green.

- [ ] **Step 6: Suggested commit (user commits)**

`feat(rules): priority allocation and product filtering (AC2, AC3)`

---

### Task 7: Financial time machine (AC4)

Deliverable: `backtest()` replays a monthly amount on the last 12 complete months of real transactions and flags months where the transfer would have broken the minimum balance. These tests are the **shared test suite for the M3 dual implementation** (AGENTS.md section 11): they use only the public signature of `backtest` and its result dataclasses, so both dual branches can run them unchanged. Do not import private helpers from `rules.backtest` in tests.

**Files:**
- Create: `backend/rules/backtest.py`, `backend/tests/rules/test_backtest.py`
- Modify: `backend/tests/conftest.py` (Hypothesis profile), `docs/traceability.md` (AC4 → `passing`), `CHANGELOG.md`

**Interfaces:**
- Consumes: `Txn`, `RuleParams`, `month_of`, `add_months` (Task 3)
- Produces:
  - `rules.backtest.BacktestMonth(month: date, balance_before_transfer: Huf, transfer: Huf, skipped: bool, balance_after: Huf, saved_to_date: Huf)`
  - `rules.backtest.BacktestResult(months: tuple[BacktestMonth, ...], total_saved: Huf, skipped_months: tuple[date, ...])`
  - `rules.backtest.backtest(transactions: Sequence[Txn], current_balance: Huf, monthly_amount: Huf, today: date, params: RuleParams = DEFAULTS) -> BacktestResult` (raises `ValueError` if `monthly_amount <= 0`)

- [ ] **Step 1: Allow Hypothesis with the autouse fixture**

The autouse `fixed_today` fixture is function-scoped; Hypothesis refuses that by default. It is harmless here (it only sets a constant), so register a profile. Add to the top of `backend/tests/conftest.py` (after the imports):

```python
from hypothesis import HealthCheck
from hypothesis import settings as hypothesis_settings

hypothesis_settings.register_profile(
    "saverai", suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
hypothesis_settings.load_profile("saverai")
```

- [ ] **Step 2: Write the failing tests**

`backend/tests/rules/test_backtest.py`:

```python
from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from rules.backtest import backtest
from rules.defaults import DEFAULTS
from rules.money import Huf
from rules.months import add_months
from rules.types import Txn
from tests.constants import TODAY

FIRST_MONTH = date(2025, 10, 1)  # 12 complete months before TODAY: Oct 2025 – Sep 2026


def steady_year(extra: list[Txn] | None = None, *, months: int = 12) -> list[Txn]:
    """Salary +400,000 and spending -400,000 every month: net 0."""
    start = add_months(FIRST_MONTH, 12 - months)
    txns: list[Txn] = []
    for i in range(months):
        month = add_months(start, i)
        txns += [Txn(month.replace(day=10), 400_000), Txn(month.replace(day=20), -400_000)]
    return txns + (extra or [])


def test_ac4_replays_twelve_months() -> None:
    result = backtest(steady_year(), current_balance=1_000_000, monthly_amount=50_000, today=TODAY)
    assert [m.month for m in result.months] == [add_months(FIRST_MONTH, i) for i in range(12)]
    assert result.total_saved == 600_000
    assert result.skipped_months == ()
    assert result.months[-1].balance_after == 400_000
    assert result.months[-1].saved_to_date == 600_000


def test_ac4_month_breaking_minimum_is_flagged_skipped() -> None:
    # Opening balance 550,000; after five transfers 300,000; March costs 150,000 extra.
    txns = steady_year([Txn(date(2026, 3, 15), -150_000)])
    result = backtest(txns, current_balance=400_000, monthly_amount=50_000, today=TODAY)
    march, april = result.months[5], result.months[6]
    assert march.month == date(2026, 3, 1)
    assert not march.skipped
    assert march.balance_after == 100_000  # leaving exactly the minimum is allowed
    assert april.skipped
    assert april.transfer == 0
    assert april.balance_after == 100_000
    assert result.skipped_months == tuple(add_months(date(2026, 4, 1), i) for i in range(6))
    assert result.total_saved == 300_000


def test_ac4_short_history_replays_available_months() -> None:
    result = backtest(steady_year(months=4), 1_000_000, 50_000, TODAY)
    assert [m.month for m in result.months] == [add_months(date(2026, 6, 1), i) for i in range(4)]
    assert result.total_saved == 200_000


def test_ac4_current_month_only_shifts_opening_balance() -> None:
    with_october = steady_year([Txn(date(2026, 10, 2), -200_000)])
    assert backtest(with_october, 800_000, 50_000, TODAY) == backtest(
        steady_year(), 1_000_000, 50_000, TODAY
    )


def test_ac4_no_transactions_gives_empty_replay() -> None:
    result = backtest([], 500_000, 50_000, TODAY)
    assert result.months == ()
    assert result.total_saved == 0


def test_backtest_rejects_non_positive_amount() -> None:
    with pytest.raises(ValueError):
        backtest(steady_year(), 1_000_000, 0, TODAY)


transactions = st.lists(
    st.builds(
        Txn,
        booked_on=st.dates(min_value=date(2025, 6, 1), max_value=date(2026, 10, 31)),
        amount=st.integers(min_value=-500_000, max_value=500_000),
    ),
    max_size=60,
)


@given(
    txns=transactions,
    balance=st.integers(min_value=-200_000, max_value=3_000_000),
    amount=st.integers(min_value=1, max_value=300_000),
)
def test_transfer_never_breaks_minimum_balance(txns: list[Txn], balance: Huf, amount: Huf) -> None:
    result = backtest(txns, balance, amount, TODAY)
    assert len(result.months) <= DEFAULTS.backtest_months
    for month in result.months:
        if month.skipped:
            assert month.transfer == 0
            assert month.balance_after == month.balance_before_transfer
            assert month.balance_before_transfer - amount < DEFAULTS.min_balance
        else:
            assert month.transfer == amount
            assert month.balance_after >= DEFAULTS.min_balance
    assert result.total_saved == sum(m.transfer for m in result.months)
    assert result.skipped_months == tuple(m.month for m in result.months if m.skipped)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/rules/test_backtest.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'rules.backtest'`.

- [ ] **Step 4: Implement**

`backend/rules/backtest.py`:

```python
"""Financial time machine: replay a plan on the customer's past transactions (AC4).

Shared contract for the dual implementation (AGENTS.md section 11): keep the signature of
`backtest` and the result dataclasses unchanged. Shows past behaviour only, not a forecast.
Principal only: no product returns, no inflation (ADR-0002).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from rules.defaults import DEFAULTS, RuleParams
from rules.money import Huf
from rules.months import add_months, month_of
from rules.types import Txn


@dataclass(frozen=True)
class BacktestMonth:
    month: date
    balance_before_transfer: Huf
    transfer: Huf  # 0 when skipped
    skipped: bool
    balance_after: Huf
    saved_to_date: Huf


@dataclass(frozen=True)
class BacktestResult:
    months: tuple[BacktestMonth, ...]
    total_saved: Huf
    skipped_months: tuple[date, ...]


def backtest(
    transactions: Sequence[Txn],
    current_balance: Huf,
    monthly_amount: Huf,
    today: date,
    params: RuleParams = DEFAULTS,
) -> BacktestResult:
    """Replay `monthly_amount` on the last `backtest_months` complete months.

    The opening balance is rebuilt backwards from `current_balance` (all transactions, own
    transfers included, move the balance). Each month: apply that month's transactions, then
    transfer at month end unless the balance would drop below `min_balance` → skipped (AC4).
    Months before the first transaction are left out.
    """
    if monthly_amount <= 0:
        raise ValueError("monthly_amount must be positive")
    current = month_of(today)
    window = [add_months(current, -n) for n in range(params.backtest_months, 0, -1)]
    if transactions:
        first_data = min(month_of(t.booked_on) for t in transactions)
        window = [m for m in window if m >= first_data]
    else:
        window = []
    if not window:
        return BacktestResult((), 0, ())

    balance = current_balance - sum(t.amount for t in transactions if t.booked_on >= window[0])
    saved = 0
    months: list[BacktestMonth] = []
    for month in window:
        balance += sum(t.amount for t in transactions if month_of(t.booked_on) == month)
        before = balance
        skipped = before - monthly_amount < params.min_balance
        transfer = 0 if skipped else monthly_amount
        balance -= transfer
        saved += transfer
        months.append(BacktestMonth(month, before, transfer, skipped, balance, saved))
    skipped_months = tuple(m.month for m in months if m.skipped)
    return BacktestResult(tuple(months), saved, skipped_months)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/rules/test_backtest.py -v`
Expected: 7 passed.

- [ ] **Step 6: Docs and check**

In `docs/traceability.md` set AC4 to `passing`. Add to `CHANGELOG.md` under `### Added`:

```markdown
- Financial time machine: replays the plan on the last 12 complete months and flags skipped months below the 100,000 HUF minimum; Hypothesis property test (AC4, ADR-0002).
```

Run: `make fmt && make check`. Expected: green.

- [ ] **Step 7: Suggested commit (user commits)**

`feat(rules): financial time machine with skipped months (AC4)`

---

### Task 8: Mandate check (golden rule 6)

Deliverable: `check_action()` allows or denies one transfer against a mandate and names the version and clause that decided it.

**Files:**
- Create: `backend/rules/mandate.py`, `backend/tests/rules/test_mandate.py`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Produces:
  - `rules.mandate.CLAUSES: dict[int, str]`; constants `AUTHORISING_CLAUSE = 1`, `MIN_BALANCE_CLAUSE = 2`, `APPROVAL_CLAUSE = 3`, `PAUSE_CLAUSE = 4`
  - `rules.mandate.MandateTerms(version: int, active: bool, max_monthly_amount: Huf, min_balance: Huf, allowed_product_ids: frozenset[int], per_transfer_approval: bool)`
  - `rules.mandate.TransferAction(product_id: int, amount: Huf, balance_before: Huf, transferred_this_month: Huf, approved_by_customer: bool)`
  - `rules.mandate.Decision(allowed: bool, mandate_version: int, clause: int, reason: str)`
  - `rules.mandate.check_action(mandate: MandateTerms, action: TransferAction) -> Decision`

- [ ] **Step 1: Write the failing tests**

`backend/tests/rules/test_mandate.py`:

```python
from dataclasses import replace

from hypothesis import given
from hypothesis import strategies as st

from rules.mandate import (
    APPROVAL_CLAUSE,
    AUTHORISING_CLAUSE,
    CLAUSES,
    MIN_BALANCE_CLAUSE,
    PAUSE_CLAUSE,
    MandateTerms,
    TransferAction,
    check_action,
)

MANDATE = MandateTerms(
    version=3,
    active=True,
    max_monthly_amount=73_500,
    min_balance=100_000,
    allowed_product_ids=frozenset({2, 4}),
    per_transfer_approval=False,
)
ACTION = TransferAction(
    product_id=4,
    amount=73_500,
    balance_before=500_000,
    transferred_this_month=0,
    approved_by_customer=False,
)


def test_transfer_within_mandate_is_allowed_by_clause_1() -> None:
    decision = check_action(MANDATE, ACTION)
    assert decision.allowed
    assert (decision.mandate_version, decision.clause) == (3, AUTHORISING_CLAUSE)


def test_paused_mandate_denies_everything() -> None:
    decision = check_action(replace(MANDATE, active=False), ACTION)
    assert not decision.allowed
    assert decision.clause == PAUSE_CLAUSE


def test_product_outside_mandate_is_denied() -> None:
    decision = check_action(MANDATE, replace(ACTION, product_id=1))
    assert (decision.allowed, decision.clause) == (False, AUTHORISING_CLAUSE)


def test_monthly_maximum_counts_earlier_transfers() -> None:
    decision = check_action(MANDATE, replace(ACTION, amount=10_000, transferred_this_month=70_000))
    assert (decision.allowed, decision.clause) == (False, AUTHORISING_CLAUSE)


def test_non_positive_amount_is_denied() -> None:
    assert not check_action(MANDATE, replace(ACTION, amount=0)).allowed


def test_balance_below_minimum_is_denied_by_clause_2() -> None:
    decision = check_action(MANDATE, replace(ACTION, balance_before=173_499))
    assert (decision.allowed, decision.clause) == (False, MIN_BALANCE_CLAUSE)


def test_leaving_exactly_the_minimum_is_allowed() -> None:
    assert check_action(MANDATE, replace(ACTION, balance_before=173_500)).allowed


def test_ac6_transfer_without_approval_is_denied_by_clause_3() -> None:
    mandate = replace(MANDATE, per_transfer_approval=True)
    decision = check_action(mandate, ACTION)
    assert (decision.allowed, decision.clause) == (False, APPROVAL_CLAUSE)
    assert check_action(mandate, replace(ACTION, approved_by_customer=True)).allowed


mandates = st.builds(
    MandateTerms,
    version=st.integers(min_value=1, max_value=10),
    active=st.booleans(),
    max_monthly_amount=st.integers(min_value=0, max_value=500_000),
    min_balance=st.integers(min_value=0, max_value=200_000),
    allowed_product_ids=st.frozensets(st.integers(min_value=1, max_value=5)),
    per_transfer_approval=st.booleans(),
)
actions = st.builds(
    TransferAction,
    product_id=st.integers(min_value=1, max_value=5),
    amount=st.integers(min_value=-1_000, max_value=500_000),
    balance_before=st.integers(min_value=-100_000, max_value=1_000_000),
    transferred_this_month=st.integers(min_value=0, max_value=500_000),
    approved_by_customer=st.booleans(),
)


@given(mandate=mandates, action=actions)
def test_allowed_transfer_respects_every_clause(
    mandate: MandateTerms, action: TransferAction
) -> None:
    decision = check_action(mandate, action)
    assert decision.mandate_version == mandate.version
    assert decision.clause in CLAUSES
    if decision.allowed:
        assert mandate.active
        assert action.amount > 0
        assert action.product_id in mandate.allowed_product_ids
        assert action.transferred_this_month + action.amount <= mandate.max_monthly_amount
        assert action.balance_before - action.amount >= mandate.min_balance
        assert action.approved_by_customer or not mandate.per_transfer_approval
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/rules/test_mandate.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'rules.mandate'`.

- [ ] **Step 3: Implement**

`backend/rules/mandate.py`:

```python
"""Mandate: the signed, versioned limits every order execution must pass (golden rule 6)."""

from dataclasses import dataclass

from rules.money import Huf

AUTHORISING_CLAUSE = 1
MIN_BALANCE_CLAUSE = 2
APPROVAL_CLAUSE = 3
PAUSE_CLAUSE = 4

CLAUSES: dict[int, str] = {
    AUTHORISING_CLAUSE: "SaverAI may transfer only to the products listed in this mandate, "
    "at most the monthly maximum in total per calendar month.",
    MIN_BALANCE_CLAUSE: "No transfer may leave the current account below the minimum balance.",
    APPROVAL_CLAUSE: "If per-transfer approval is set, each transfer needs the customer's "
    "explicit approval.",
    PAUSE_CLAUSE: "No transfer runs while the mandate is paused.",
}


@dataclass(frozen=True)
class MandateTerms:
    version: int
    active: bool
    max_monthly_amount: Huf
    min_balance: Huf
    allowed_product_ids: frozenset[int]
    per_transfer_approval: bool


@dataclass(frozen=True)
class TransferAction:
    product_id: int
    amount: Huf
    balance_before: Huf
    transferred_this_month: Huf  # already executed under this mandate this month
    approved_by_customer: bool


@dataclass(frozen=True)
class Decision:
    allowed: bool
    mandate_version: int
    clause: int  # the clause that allowed (1) or denied the transfer
    reason: str


def check_action(mandate: MandateTerms, action: TransferAction) -> Decision:
    """Allow or deny one transfer. Checks in order: pause (§4), products and monthly maximum (§1),
    minimum balance (§2), per-transfer approval (§3, last, so "awaiting approval" only happens
    when everything else is fine)."""

    def deny(clause: int, reason: str) -> Decision:
        return Decision(False, mandate.version, clause, reason)

    if not mandate.active:
        return deny(PAUSE_CLAUSE, "The mandate is paused.")
    if action.amount <= 0:
        return deny(AUTHORISING_CLAUSE, "The transfer amount must be positive.")
    if action.product_id not in mandate.allowed_product_ids:
        return deny(AUTHORISING_CLAUSE, "The product is not listed in the mandate.")
    if action.transferred_this_month + action.amount > mandate.max_monthly_amount:
        return deny(AUTHORISING_CLAUSE, "The monthly maximum would be exceeded.")
    if action.balance_before - action.amount < mandate.min_balance:
        return deny(MIN_BALANCE_CLAUSE, "The balance would drop below the minimum.")
    if mandate.per_transfer_approval and not action.approved_by_customer:
        return deny(APPROVAL_CLAUSE, "This transfer needs your approval.")
    return Decision(True, mandate.version, AUTHORISING_CLAUSE, "Within the mandate.")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/rules/test_mandate.py -v`
Expected: 9 passed.

- [ ] **Step 5: Docs and check**

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Mandate check `check_action()` with numbered clauses (§1 products and monthly maximum, §2 minimum balance, §3 per-transfer approval, §4 pause); Hypothesis property test.
```

Run: `make fmt && make check`. Expected: green.

- [ ] **Step 6: Suggested commit (user commits)**

`feat(rules): mandate check with versioned clauses`

---

### Task 9: Data model, RuleConfig, Django admin, architecture doc

Deliverable: migrated models for the simulated bank and the plan lifecycle, `RuleConfig.load()` returning `RuleParams`, admin for products and rule parameters. **Data model change: the user approves it by approving this plan (AGENTS.md section 9).**

**Files:**
- Modify: `backend/banking/models.py`, `backend/plans/models.py`
- Create: `backend/banking/admin.py`, `backend/plans/admin.py`, migrations (generated), `backend/tests/services/__init__.py`, `backend/tests/services/test_models.py`, `docs/architecture.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `Txn`, `ProductInfo` (Task 3), `RuleParams`, `DEFAULTS` (Task 3), `Confidence`, `needs_per_transfer_approval` (Task 5), `MandateTerms` (Task 8)
- Produces (Django models; all money fields `BigIntegerField`, all timestamps set from the `Clock`, never `auto_now`):
  - `banking.Account(customer: OneToOne User related_name="account", name, balance)`
  - `banking.Transaction(account FK related_name="transactions", booked_on, amount, description, own_transfer)` + `to_rule() -> Txn`
  - `banking.Product(code unique, name, risk_level 1–5 (DB check), min_horizon_months, liquid, active)` + `to_rule() -> ProductInfo`
  - `plans.RuleConfig` (singleton pk=1, one field per `RuleParams` field) + `RuleConfig.load() -> RuleParams`
  - `plans.QuestionnaireAnswer(customer, risk_score, existing_emergency_fund, expected_monthly_savings: null, submitted_at)`; `plans.ExpenseAnswer(questionnaire FK related_name="expenses", name, amount, due_on)`
  - `plans.Plan(customer, questionnaire, status: Plan.Status PROPOSED/ACCEPTED/REJECTED/PAUSED, monthly_amount, proposed_amount, median_surplus: null, median_expenses, months_of_data, confidence, created_at)` + property `per_transfer_approval -> bool`
  - `plans.PlanItem(plan FK related_name="items", position, kind, label, product FK PROTECT, monthly_amount, target_amount: null)`
  - `plans.Mandate(customer, plan OneToOne related_name="mandate", version, status: Mandate.Status ACTIVE/PAUSED, max_monthly_amount, min_balance, per_transfer_approval, products M2M, signed_at)`; unique (customer, version); `terms() -> MandateTerms`
  - `plans.RecurringOrder(plan_item OneToOne related_name="order", mandate FK related_name="orders", product FK, monthly_amount, status: RecurringOrder.Status ACTIVE/PAUSED)`
  - `plans.Execution(order FK related_name="executions", period (first of month), idempotency_key unique, status: Execution.Status EXECUTED/DENIED/AWAITING_APPROVAL, amount, mandate_version, clause, reason, created_at)`
  - `plans.LogEntry(customer, plan FK null, event, message, mandate_version null, clause null, created_at)`

- [ ] **Step 1: Write the failing tests**

Create empty `backend/tests/services/__init__.py`.

`backend/tests/services/test_models.py`:

```python
from dataclasses import fields

import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction

from banking.models import Account, Product, Transaction
from plans.models import RuleConfig
from rules.defaults import DEFAULTS
from tests.constants import TODAY

pytestmark = pytest.mark.django_db


def test_rule_config_defaults_match_rules_defaults() -> None:
    assert RuleConfig.load() == DEFAULTS
    assert {f.name for f in fields(DEFAULTS)} <= {f.name for f in RuleConfig._meta.fields}


def test_rule_config_is_a_singleton_and_changes_are_used() -> None:
    config = RuleConfig.objects.create(monthly_share_percent=60)
    config.save()
    RuleConfig(monthly_share_percent=60).save()
    assert RuleConfig.objects.count() == 1
    assert RuleConfig.load().monthly_share_percent == 60


def test_product_risk_level_above_5_is_rejected() -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Product.objects.create(code="x", name="X", risk_level=6)


def test_models_convert_to_rule_types() -> None:
    user = User.objects.create_user(username="anna", password="pw")
    account = Account.objects.create(customer=user, balance=500_000)
    txn = Transaction.objects.create(
        account=account, booked_on=TODAY, amount=-1_000, description="Coffee", own_transfer=False
    )
    product = Product.objects.create(
        code="mm", name="Money market fund", risk_level=1, min_horizon_months=0, liquid=True
    )
    assert txn.to_rule().amount == -1_000
    assert product.to_rule().liquid
    assert product.to_rule().id == product.pk
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/services/test_models.py`
Expected: FAIL with `ImportError: cannot import name 'Account' from 'banking.models'`.

- [ ] **Step 3: Implement the banking models**

`backend/banking/models.py`:

```python
"""Simulated bank: current accounts, their transactions and the product catalogue."""

from django.conf import settings
from django.db import models

from rules.types import ProductInfo, Txn


class Account(models.Model):
    """A customer's simulated current account. Balance in whole forints."""

    customer = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="account"
    )
    name = models.CharField(max_length=100, default="Current account")
    balance = models.BigIntegerField()

    def __str__(self) -> str:
        return f"{self.customer} – {self.name}"


class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
    booked_on = models.DateField()
    amount = models.BigIntegerField(help_text="Positive: income, negative: expense (HUF).")
    description = models.CharField(max_length=200, blank=True)
    own_transfer = models.BooleanField(
        default=False,
        help_text="Between the customer's own accounts or a SaverAI transfer; ignored in surplus.",
    )

    class Meta:
        ordering = ["booked_on", "id"]

    def to_rule(self) -> Txn:
        return Txn(
            booked_on=self.booked_on,
            amount=self.amount,
            own_transfer=self.own_transfer,
            description=self.description,
        )


class Product(models.Model):
    """Catalogue entry, managed by the Admin role in Django admin."""

    code = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    risk_level = models.PositiveSmallIntegerField(help_text="1 (lowest) to 5 (highest).")
    min_horizon_months = models.PositiveSmallIntegerField(default=0)
    liquid = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["risk_level", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(risk_level__gte=1, risk_level__lte=5),
                name="product_risk_level_1_to_5",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} (risk {self.risk_level})"

    def to_rule(self) -> ProductInfo:
        return ProductInfo(
            id=self.pk,
            name=self.name,
            risk_level=self.risk_level,
            min_horizon_months=self.min_horizon_months,
            liquid=self.liquid,
        )
```

- [ ] **Step 4: Implement the plans models**

`backend/plans/models.py`:

```python
"""Questionnaire answers, plans, mandates, recurring orders, executions and the audit log."""

from dataclasses import fields
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from banking.models import Product
from rules.confidence import Confidence, needs_per_transfer_approval
from rules.defaults import DEFAULTS, RuleParams
from rules.mandate import MandateTerms

USER = settings.AUTH_USER_MODEL


def _months(default: int) -> Any:  # field classes are not subscriptable at runtime
    return models.PositiveSmallIntegerField(default=default, validators=[MinValueValidator(1)])


class RuleConfig(models.Model):
    """Rule parameters (AGENTS.md section 6). Singleton (pk=1), edited in Django admin."""

    monthly_share_percent = models.PositiveSmallIntegerField(
        default=DEFAULTS.monthly_share_percent,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    surplus_window_months = _months(DEFAULTS.surplus_window_months)
    min_months_for_estimate = _months(DEFAULTS.min_months_for_estimate)
    full_confidence_months = _months(DEFAULTS.full_confidence_months)
    emergency_fund_months = _months(DEFAULTS.emergency_fund_months)
    liquid_horizon_months = _months(DEFAULTS.liquid_horizon_months)
    low_risk_max = models.PositiveSmallIntegerField(
        default=DEFAULTS.low_risk_max, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    min_balance = models.BigIntegerField(
        default=DEFAULTS.min_balance, validators=[MinValueValidator(0)]
    )
    backtest_months = _months(DEFAULTS.backtest_months)

    class Meta:
        verbose_name = "rule configuration"

    def __str__(self) -> str:
        return "Rule configuration"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> RuleParams:
        config, _ = cls.objects.get_or_create(pk=1)
        return RuleParams(**{f.name: getattr(config, f.name) for f in fields(RuleParams)})


class QuestionnaireAnswer(models.Model):
    customer = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="questionnaires")
    risk_score = models.PositiveSmallIntegerField()
    existing_emergency_fund = models.BigIntegerField()
    expected_monthly_savings = models.BigIntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField()


class ExpenseAnswer(models.Model):
    questionnaire = models.ForeignKey(
        QuestionnaireAnswer, on_delete=models.CASCADE, related_name="expenses"
    )
    name = models.CharField(max_length=100)
    amount = models.BigIntegerField()
    due_on = models.DateField()


class Plan(models.Model):
    class Status(models.TextChoices):
        PROPOSED = "proposed"
        ACCEPTED = "accepted"
        REJECTED = "rejected"
        PAUSED = "paused"

    customer = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="plans")
    questionnaire = models.ForeignKey(QuestionnaireAnswer, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PROPOSED)
    monthly_amount = models.BigIntegerField()
    proposed_amount = models.BigIntegerField(help_text="Rule-engine amount; edits may only lower it.")
    median_surplus = models.BigIntegerField(null=True, blank=True)
    median_expenses = models.BigIntegerField()
    months_of_data = models.PositiveSmallIntegerField()
    confidence = models.CharField(max_length=10, choices=[(c.value, c.value) for c in Confidence])
    created_at = models.DateTimeField()

    @property
    def per_transfer_approval(self) -> bool:
        return needs_per_transfer_approval(Confidence(self.confidence))


class PlanItem(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="items")
    position = models.PositiveSmallIntegerField()
    kind = models.CharField(max_length=20)
    label = models.CharField(max_length=100)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    monthly_amount = models.BigIntegerField()
    target_amount = models.BigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["plan", "position"], name="plan_item_position_unique")
        ]


class Mandate(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active"
        PAUSED = "paused"

    customer = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="mandates")
    plan = models.OneToOneField(Plan, on_delete=models.PROTECT, related_name="mandate")
    version = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    max_monthly_amount = models.BigIntegerField()
    min_balance = models.BigIntegerField()
    per_transfer_approval = models.BooleanField()
    products = models.ManyToManyField(Product)
    signed_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["customer", "version"], name="mandate_version_unique")
        ]

    def terms(self) -> MandateTerms:
        return MandateTerms(
            version=self.version,
            active=self.status == self.Status.ACTIVE,
            max_monthly_amount=self.max_monthly_amount,
            min_balance=self.min_balance,
            allowed_product_ids=frozenset(self.products.values_list("id", flat=True)),
            per_transfer_approval=self.per_transfer_approval,
        )


class RecurringOrder(models.Model):
    """One per plan item. The OneToOne field makes "exactly once" a DB guarantee (AC7)."""

    class Status(models.TextChoices):
        ACTIVE = "active"
        PAUSED = "paused"

    plan_item = models.OneToOneField(PlanItem, on_delete=models.PROTECT, related_name="order")
    mandate = models.ForeignKey(Mandate, on_delete=models.PROTECT, related_name="orders")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    monthly_amount = models.BigIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)


class Execution(models.Model):
    """One monthly run of one order. The unique idempotency key prevents duplicates (AC7)."""

    class Status(models.TextChoices):
        EXECUTED = "executed"
        DENIED = "denied"
        AWAITING_APPROVAL = "awaiting_approval"

    order = models.ForeignKey(RecurringOrder, on_delete=models.PROTECT, related_name="executions")
    period = models.DateField(help_text="First day of the month this execution belongs to.")
    idempotency_key = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    amount = models.BigIntegerField()
    mandate_version = models.PositiveIntegerField()
    clause = models.PositiveSmallIntegerField()
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField()


class LogEntry(models.Model):
    customer = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="log_entries")
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    event = models.CharField(max_length=50)
    message = models.TextField()
    mandate_version = models.PositiveIntegerField(null=True, blank=True)
    clause = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        ordering = ["created_at", "id"]
```

Never write `models.SomeField[...]` or `admin.ModelAdmin[...]` in runtime code: Django 5.2 raises `TypeError: type ... is not subscriptable` at import (verified while writing this plan).

- [ ] **Step 5: Admin**

`backend/banking/admin.py`:

```python
"""Admin role: product catalogue; accounts and transactions for inspection."""

from django.contrib import admin

from banking.models import Account, Product, Transaction


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "risk_level", "min_horizon_months", "liquid", "active"]
    list_filter = ["risk_level", "liquid", "active"]


admin.site.register(Account)
admin.site.register(Transaction)
```

`backend/plans/admin.py`:

```python
"""Admin role: rule parameters; plans, mandates, executions and the log for inspection."""

from django.contrib import admin

from plans.models import Execution, LogEntry, Mandate, Plan, RuleConfig


@admin.register(RuleConfig)
class RuleConfigAdmin(admin.ModelAdmin):
    def has_add_permission(self, request: object) -> bool:
        return not RuleConfig.objects.exists()

    def has_delete_permission(self, request: object, obj: RuleConfig | None = None) -> bool:
        return False


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ["created_at", "customer", "event", "mandate_version", "clause"]


admin.site.register(Plan)
admin.site.register(Mandate)
admin.site.register(Execution)
```

If mypy complains about the `request` parameter type, use `django.http.HttpRequest`.

- [ ] **Step 6: Generate migrations and run tests**

Run: `cd backend && uv run python manage.py makemigrations banking plans && uv run pytest tests/services/test_models.py -v`
Expected: migrations `banking/migrations/0001_initial.py`, `plans/migrations/0001_initial.py` created; 4 passed.

- [ ] **Step 7: Architecture document**

Create `docs/architecture.md`:

```markdown
# Architecture

## Components
- `backend/rules/` — pure rule engine (no Django): surplus (AC1, AC5), confidence (AC6), plan
  allocation (AC2, AC3), time machine (AC4), mandate check.
- `backend/banking/` — simulated bank: accounts, transactions, product catalogue, synthetic data.
- `backend/plans/` — questionnaire, plans, mandates, recurring orders, executions, audit log,
  explanation templates, services.
- `backend/api/` — Django Ninja JSON API (session login, input validation, ownership checks).
- `backend/core/clock.py` — injected time source.
- Django admin — Admin role: products and `RuleConfig`.

Dependency direction: `api` → `plans` / `banking` → `rules`. `banking` never imports `plans`.

## Data model
| Model | Purpose | Key constraints |
| --- | --- | --- |
| `banking.Account` | One simulated current account per customer, `balance` in HUF | OneToOne customer |
| `banking.Transaction` | Booked income (+) / expense (−); `own_transfer` excluded from surplus | — |
| `banking.Product` | Catalogue: risk 1–5, minimum horizon, liquid, active | check risk 1–5, unique code |
| `plans.RuleConfig` | Rule parameters, singleton, defaults from `rules/defaults.py` | pk = 1 |
| `plans.QuestionnaireAnswer` / `ExpenseAnswer` | Fixed questionnaire answers and planned expenses | — |
| `plans.Plan` | Proposal snapshot: amount, medians, confidence, status proposed/accepted/rejected/paused | — |
| `plans.PlanItem` | Ordered allocation lines with product | unique (plan, position) |
| `plans.Mandate` | Signed limits, versioned per customer | unique (customer, version), OneToOne plan |
| `plans.RecurringOrder` | One per accepted plan item | OneToOne plan item (AC7) |
| `plans.Execution` | One monthly run of one order, with mandate version and clause | unique idempotency key (AC7) |
| `plans.LogEntry` | Audit log; execution entries carry mandate version and clause | — |

All money fields are `BigIntegerField` (whole forints). Timestamps come from the injected clock.

## Main flow
questionnaire → `propose_plan` (rule engine) → plan review + time machine → accept (mandate vN,
recurring orders) → `manage.py run_orders` each month → `check_action` → execution + log entry.
```

- [ ] **Step 8: Docs and check**

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Data model: accounts, transactions, products, rule configuration, questionnaire, plans, mandates, recurring orders, executions, audit log (see `docs/architecture.md`).
- Django admin for the product catalogue and rule parameters (Admin role).
```

Run: `make fmt && make check`. Expected: green.

- [ ] **Step 9: Suggested commit (user commits)**

`feat(models): bank, plan, mandate and execution models with admin`

---

### Task 10: Seed personas and catalogue (`make seed`)

Deliverable: `make seed` loads the product catalogue, an admin user and four personas covering AC1/AC2, AC5 and AC6. Safe to re-run. Also adds DB test helpers used by later tasks.

**Files:**
- Create: `backend/banking/management/__init__.py`, `backend/banking/management/commands/__init__.py`, `backend/banking/management/commands/seed.py`, `backend/tests/factories.py`, `backend/tests/services/test_seed.py`
- Modify: `Makefile`, `README.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `monthly_series` (Task 4), banking models (Task 9), `get_clock` (Task 3). Must not import `plans` (dependency direction); `RuleConfig` creates itself on first `load()`.
- Produces:
  - `banking.management.commands.seed.PRODUCTS: list[tuple[str, str, int, int, bool]]` (code, name, risk, min horizon, liquid) and `PERSONAS: list[tuple[str, list[int], int]]` (username, surpluses oldest first, opening balance)
  - `tests.factories.create_catalogue() -> list[Product]`, `tests.factories.create_customer(username: str, surpluses: Sequence[Huf], *, balance: Huf = 1_000_000) -> User` (transactions from `monthly_series(LAST_MONTH, surpluses)`)

- [ ] **Step 1: Write the failing tests**

`backend/tests/factories.py`:

```python
"""DB test helpers. Uses the same catalogue as `make seed`."""

from collections.abc import Sequence

from django.contrib.auth.models import User

from banking.management.commands.seed import PRODUCTS
from banking.models import Account, Product, Transaction
from banking.synthetic import monthly_series
from rules.money import Huf
from tests.constants import LAST_MONTH


def create_catalogue() -> list[Product]:
    return [
        Product.objects.create(
            code=code, name=name, risk_level=risk, min_horizon_months=horizon, liquid=liquid
        )
        for code, name, risk, horizon, liquid in PRODUCTS
    ]


def create_customer(username: str, surpluses: Sequence[Huf], *, balance: Huf = 1_000_000) -> User:
    user = User.objects.create_user(username=username, password="pw")
    account = Account.objects.create(customer=user, balance=balance)
    Transaction.objects.bulk_create(
        [
            Transaction(
                account=account,
                booked_on=t.booked_on,
                amount=t.amount,
                description=t.description,
                own_transfer=t.own_transfer,
            )
            for t in monthly_series(LAST_MONTH, surpluses)
        ]
    )
    return user
```

`backend/tests/services/test_seed.py`:

```python
import pytest
from django.contrib.auth.models import User
from django.core.management import CommandError, call_command

from banking.models import Account, Product, Transaction
from rules.surplus import analyse_surplus
from tests.constants import TODAY

pytestmark = pytest.mark.django_db


@pytest.fixture
def seed_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEED_PASSWORD", "demo-only")


@pytest.mark.usefixtures("seed_password")
def test_seed_is_safe_to_run_twice() -> None:
    call_command("seed")
    call_command("seed")
    assert User.objects.filter(username="anna").count() == 1
    assert Transaction.objects.filter(account__customer__username="anna").count() == 24
    assert Product.objects.count() == 5
    assert User.objects.get(username="admin").is_staff


@pytest.mark.usefixtures("seed_password")
def test_seeded_anna_gives_the_ac1_amount() -> None:
    call_command("seed")
    txns = [t.to_rule() for t in Transaction.objects.filter(account__customer__username="anna")]
    assert analyse_surplus(txns, TODAY).monthly_amount == 73_500


@pytest.mark.usefixtures("seed_password")
def test_seeded_balance_matches_transactions() -> None:
    call_command("seed")
    account = Account.objects.get(customer__username="anna")
    total = sum(t.amount for t in account.transactions.all())
    assert account.balance == 600_000 + total


def test_seed_without_password_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SEED_PASSWORD", raising=False)
    with pytest.raises(CommandError):
        call_command("seed")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/services/test_seed.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'banking.management'`.

- [ ] **Step 3: Implement the seed command**

Create empty `backend/banking/management/__init__.py` and `backend/banking/management/commands/__init__.py`.

`backend/banking/management/commands/seed.py`:

```python
"""Load the product catalogue, the admin user and synthetic personas. Safe to re-run:
existing users are left unchanged. Dates are relative to the injected clock."""

import os
from typing import Any

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from banking.models import Account, Product, Transaction
from banking.synthetic import monthly_series
from core.clock import get_clock
from rules.months import add_months, month_of

# code, name, risk level, minimum horizon (months), liquid
PRODUCTS: list[tuple[str, str, int, int, bool]] = [
    ("money-market", "Money market fund", 1, 0, True),
    ("short-bond", "Short government bond fund", 2, 0, True),
    ("gov-bond-3y", "3-year government bond", 2, 24, False),
    ("balanced", "Balanced fund", 3, 36, False),
    ("equity", "Global equity fund", 5, 60, False),
]

# username, monthly surpluses (oldest first, ending last month), opening balance
PERSONAS: list[tuple[str, list[int], int]] = [
    ("anna", [100_000, 120_000, 80_000, 110_000, 90_000, 300_000], 600_000),  # AC1, AC2
    ("bence", [-40_000] * 6, 300_000),  # AC5: no surplus
    ("csilla", [60_000, 70_000], 400_000),  # AC6: 2 months → no estimate
    ("dani", [50_000, 60_000, 55_000, 65_000], 400_000),  # AC6: 4 months → low confidence
]


class Command(BaseCommand):
    help = "Load synthetic personas, the product catalogue and the admin user."

    def handle(self, *args: Any, **options: Any) -> None:
        password = os.environ.get("SEED_PASSWORD")
        if not password:
            raise CommandError("Set SEED_PASSWORD in .env (see .env.example).")
        last_month = add_months(month_of(get_clock().today()), -1)
        with transaction.atomic():
            for code, name, risk, horizon, liquid in PRODUCTS:
                Product.objects.update_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "risk_level": risk,
                        "min_horizon_months": horizon,
                        "liquid": liquid,
                    },
                )
            if not User.objects.filter(username="admin").exists():
                User.objects.create_superuser(username="admin", password=password)
            for username, surpluses, opening in PERSONAS:
                if User.objects.filter(username=username).exists():
                    continue
                user = User.objects.create_user(username=username, password=password)
                txns = monthly_series(last_month, surpluses)
                account = Account.objects.create(
                    customer=user, balance=opening + sum(t.amount for t in txns)
                )
                Transaction.objects.bulk_create(
                    [
                        Transaction(
                            account=account,
                            booked_on=t.booked_on,
                            amount=t.amount,
                            description=t.description,
                            own_transfer=t.own_transfer,
                        )
                        for t in txns
                    ]
                )
        self.stdout.write(
            self.style.SUCCESS(f"Seeded {len(PRODUCTS)} products and {len(PERSONAS)} personas.")
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/services/test_seed.py -v`
Expected: 4 passed.

- [ ] **Step 5: Makefile, README, changelog**

In `Makefile` add `seed` to `.PHONY` and add:

```make
seed: migrate
	cd backend && uv run python manage.py seed
```

In `README.md` under "Setup and run", after `make migrate`, add:

```
    make seed       # products, admin user and demo personas (password: SEED_PASSWORD in .env)
```

and add a section:

```markdown
## Demo personas (`make seed`)
| User | Data | Shows |
| --- | --- | --- |
| anna | 6 months, surpluses 100k/120k/80k/110k/90k/300k | AC1 (73,500 HUF), AC2 when no emergency fund is entered |
| bence | 6 months, −40k each | AC5 no surplus |
| csilla | 2 months | AC6 asks for expected savings |
| dani | 4 months | AC6 low confidence, per-transfer approval |
| admin | staff user | Django admin: products, rule parameters |
```

Add to `CHANGELOG.md` under `### Added`:

```markdown
- `make seed`: product catalogue, admin user and personas for AC1, AC2, AC5 and AC6.
```

Run: `make fmt && make check`. Expected: green.

- [ ] **Step 6: Suggested commit (user commits)**

`feat(banking): seed command with demo personas and catalogue`

---

### Task 11: Explanation templates and plan services (AC5, AC6, AC7, AC8 service side)

Deliverable: fixed explanation templates, and services that store questionnaires, run the rule engine, and accept / reject / edit / pause plans. Acceptance signs a versioned mandate and creates recurring orders exactly once.

**Files:**
- Create: `backend/plans/explanations.py`, `backend/plans/services.py`, `backend/tests/services/test_explanations.py`, `backend/tests/services/test_acceptance.py`
- Modify: `docs/traceability.md` (AC7 stays `planned` until Task 12 adds the execution test), `CHANGELOG.md`

**Interfaces:**
- Consumes: `propose`, `allocate`, `Outcome`, `NoEligibleProduct`, `PlanInputs`, `Proposal` (Task 6); `backtest`, `BacktestResult` (Task 7); `analyse_surplus`, `SurplusAnalysis` (Task 4); `Confidence`, `assess_confidence` (Task 5); models (Task 9); `Clock` (Task 3); `create_catalogue`, `create_customer` (Task 10)
- Produces:
  - `plans.explanations`: `huf(amount: Huf) -> str` ("73,500"), `no_surplus(months: int, median: Huf) -> str`, `needs_expected_savings(months: int, required: int) -> str`, `plan_summary(*, amount: Huf, median_surplus: Huf | None, percent: int, months_of_data: int, confidence: Confidence) -> list[str]`, `skipped_month(month: date, minimum: Huf) -> str`
  - `plans.services.InvalidInput(Exception)` (→ HTTP 422), `plans.services.PlanConflict(Exception)` (→ HTTP 409)
  - `log_event(customer: User, event: str, message: str, clock: Clock, *, plan: Plan | None = None, mandate_version: int | None = None, clause: int | None = None) -> LogEntry`
  - `submit_questionnaire(customer: User, *, risk_score: int, existing_emergency_fund: Huf, expected_monthly_savings: Huf | None, planned_expenses: Sequence[PlannedExpense], clock: Clock) -> QuestionnaireAnswer`
  - `analyse(customer: User, clock: Clock) -> tuple[SurplusAnalysis, Confidence]`
  - `propose_plan(customer: User, clock: Clock) -> tuple[Proposal, Plan | None]`
  - `get_owned_plan(customer: User, plan_id: int) -> Plan` (404 `Http404`, 403 `PermissionDenied`)
  - `accept_plan(plan: Plan, clock: Clock) -> list[RecurringOrder]`, `reject_plan(plan: Plan, clock: Clock) -> Plan`, `edit_amount(plan: Plan, monthly_amount: Huf, clock: Clock) -> Plan`, `pause_plan(plan: Plan, clock: Clock) -> Plan`, `active_plan(customer: User) -> Plan | None`, `time_machine(plan: Plan, clock: Clock) -> BacktestResult`

- [ ] **Step 1: Write the failing explanation tests**

`backend/tests/services/test_explanations.py`:

```python
from datetime import date

from plans import explanations
from rules.confidence import Confidence


def test_ac5_no_surplus_message_states_the_median() -> None:
    text = explanations.no_surplus(6, -40_000)
    assert "-40,000 HUF" in text
    assert "no surplus" in text


def test_ac6_message_asks_for_expected_savings() -> None:
    text = explanations.needs_expected_savings(2, 3)
    assert "only 2" in text
    assert "expect to save" in text


def test_plan_summary_uses_rule_results() -> None:
    lines = explanations.plan_summary(
        amount=73_500,
        median_surplus=105_000,
        percent=70,
        months_of_data=6,
        confidence=Confidence.NORMAL,
    )
    assert lines == [
        "We suggest saving 73,500 HUF a month: 70% of your median monthly surplus of 105,000 HUF."
    ]


def test_low_confidence_plan_mentions_approval() -> None:
    lines = explanations.plan_summary(
        amount=40_250, median_surplus=57_500, percent=70, months_of_data=4,
        confidence=Confidence.LOW,
    )
    assert len(lines) == 2
    assert "approval" in lines[1]


def test_skipped_month_message() -> None:
    text = explanations.skipped_month(date(2026, 4, 1), 100_000)
    assert text.startswith("2026-04")
    assert "100,000 HUF" in text
```

- [ ] **Step 2: Run to verify failure, then implement templates**

Run: `cd backend && uv run pytest tests/services/test_explanations.py`
Expected: FAIL with `ImportError: cannot import name 'explanations' from 'plans'`.

`backend/plans/explanations.py`:

```python
"""Fixed explanation templates (golden rule 2). They only format rule-engine results;
they never compute amounts, dates or decisions."""

from datetime import date

from rules.confidence import Confidence
from rules.money import Huf

NO_SURPLUS = (
    "Your median monthly surplus over the last {months} months is {median} HUF, so there is "
    "no surplus to save. No investment plan was created."
)
NEEDS_EXPECTED_SAVINGS = (
    "We found only {months} full months of transactions; at least {required} are needed for an "
    "estimate. Please enter how much you expect to save each month."
)
PLAN_FROM_SURPLUS = (
    "We suggest saving {amount} HUF a month: {percent}% of your median monthly surplus of "
    "{median} HUF."
)
PLAN_FROM_EXPECTED = (
    "We suggest saving {amount} HUF a month, the amount you said you expect to save."
)
LOW_CONFIDENCE = (
    "This plan is based on only {months} months of data, so its confidence is low. "
    "Every transfer will ask for your approval."
)
SKIPPED_MONTH = (
    "{month}: the transfer was skipped because it would have left less than {minimum} HUF "
    "on your account."
)


def huf(amount: Huf) -> str:
    return f"{amount:,}"


def no_surplus(months: int, median: Huf) -> str:
    return NO_SURPLUS.format(months=months, median=huf(median))


def needs_expected_savings(months: int, required: int) -> str:
    return NEEDS_EXPECTED_SAVINGS.format(months=months, required=required)


def plan_summary(
    *,
    amount: Huf,
    median_surplus: Huf | None,
    percent: int,
    months_of_data: int,
    confidence: Confidence,
) -> list[str]:
    if median_surplus is None:
        lines = [PLAN_FROM_EXPECTED.format(amount=huf(amount))]
    else:
        lines = [
            PLAN_FROM_SURPLUS.format(amount=huf(amount), percent=percent, median=huf(median_surplus))
        ]
    if confidence is not Confidence.NORMAL:
        lines.append(LOW_CONFIDENCE.format(months=months_of_data))
    return lines


def skipped_month(month: date, minimum: Huf) -> str:
    return SKIPPED_MONTH.format(month=f"{month:%Y-%m}", minimum=huf(minimum))
```

Run: `cd backend && uv run pytest tests/services/test_explanations.py -v`
Expected: 5 passed.

- [ ] **Step 3: Write the failing service tests**

`backend/tests/services/test_acceptance.py`:

```python
from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import Http404

from banking.models import Product
from core.clock import FixedClock
from plans.models import LogEntry, Mandate, Plan, QuestionnaireAnswer, RecurringOrder
from plans.services import (
    InvalidInput,
    PlanConflict,
    accept_plan,
    active_plan,
    edit_amount,
    get_owned_plan,
    pause_plan,
    propose_plan,
    reject_plan,
    submit_questionnaire,
    time_machine,
)
from rules.money import Huf
from rules.plan import Outcome
from rules.types import PlannedExpense
from tests.constants import AC1_SERIES, TODAY
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def answer(
    customer: User,
    clock: FixedClock,
    *,
    fund: Huf = 0,
    expected: Huf | None = None,
    expenses: tuple[PlannedExpense, ...] = (),
) -> QuestionnaireAnswer:
    return submit_questionnaire(
        customer,
        risk_score=3,
        existing_emergency_fund=fund,
        expected_monthly_savings=expected,
        planned_expenses=expenses,
        clock=clock,
    )


def proposed_plan(clock: FixedClock, username: str = "anna", fund: Huf = 0) -> Plan:
    customer = create_customer(username, AC1_SERIES)
    answer(customer, clock, fund=fund)
    _, plan = propose_plan(customer, clock)
    assert plan is not None
    return plan


def test_proposal_stores_plan_with_emergency_fund_first(clock: FixedClock) -> None:
    plan = proposed_plan(clock)
    assert plan.status == Plan.Status.PROPOSED
    assert plan.monthly_amount == 73_500
    assert [item.kind for item in plan.items.all()] == ["emergency_fund"]
    assert LogEntry.objects.filter(event="plan_proposed").count() == 1


def test_ac5_no_surplus_stores_no_plan(clock: FixedClock) -> None:
    customer = create_customer("bence", [-40_000] * 6)
    answer(customer, clock)
    proposal, plan = propose_plan(customer, clock)
    assert proposal.outcome is Outcome.NO_SURPLUS
    assert plan is None
    assert Plan.objects.count() == 0


def test_ac6_short_history_stores_no_plan_without_expected_savings(clock: FixedClock) -> None:
    customer = create_customer("csilla", [60_000, 70_000])
    answer(customer, clock)
    proposal, plan = propose_plan(customer, clock)
    assert proposal.outcome is Outcome.NEEDS_EXPECTED_SAVINGS
    assert plan is None


def test_proposal_without_questionnaire_is_a_conflict(clock: FixedClock) -> None:
    with pytest.raises(PlanConflict):
        propose_plan(create_customer("anna", AC1_SERIES), clock)


def test_ac7_accepting_twice_creates_orders_once(clock: FixedClock) -> None:
    plan = proposed_plan(clock, fund=700_000)  # two items: emergency fund + investment
    first = accept_plan(plan, clock)
    second = accept_plan(plan, clock)
    assert len(first) == 2
    assert {o.pk for o in second} == {o.pk for o in first}
    assert RecurringOrder.objects.count() == 2
    assert Mandate.objects.count() == 1
    assert LogEntry.objects.filter(event="plan_accepted").count() == 1


def test_ac7_rejected_plan_creates_no_orders(clock: FixedClock) -> None:
    plan = proposed_plan(clock)
    reject_plan(plan, clock)
    with pytest.raises(PlanConflict):
        accept_plan(plan, clock)
    assert RecurringOrder.objects.count() == 0
    assert Mandate.objects.count() == 0


def test_acceptance_signs_a_new_mandate_version(clock: FixedClock) -> None:
    plan = proposed_plan(clock)
    accept_plan(plan, clock)
    pause_plan(plan, clock)
    _, second = propose_plan(plan.customer, clock)
    assert second is not None
    accept_plan(second, clock)
    assert sorted(Mandate.objects.values_list("version", flat=True)) == [1, 2]


def test_second_active_plan_is_a_conflict(clock: FixedClock) -> None:
    plan = proposed_plan(clock)
    accept_plan(plan, clock)
    _, second = propose_plan(plan.customer, clock)
    assert second is not None
    with pytest.raises(PlanConflict):
        accept_plan(second, clock)


def test_edit_amount_reallocates_and_stays_proposed(clock: FixedClock) -> None:
    plan = edit_amount(proposed_plan(clock, fund=700_000), 50_000, clock)
    assert plan.status == Plan.Status.PROPOSED
    assert sum(item.monthly_amount for item in plan.items.all()) == 50_000
    assert [item.kind for item in plan.items.all()] == ["emergency_fund"]
    assert RecurringOrder.objects.count() == 0


@pytest.mark.parametrize("amount", [0, -5, 73_501])
def test_edit_amount_outside_range_is_invalid(clock: FixedClock, amount: Huf) -> None:
    with pytest.raises(InvalidInput):
        edit_amount(proposed_plan(clock), amount, clock)


def test_ac8_past_expense_date_is_rejected_by_service(clock: FixedClock) -> None:
    customer = create_customer("anna", AC1_SERIES)
    yesterday = PlannedExpense("Car", 500_000, TODAY - timedelta(days=1))
    with pytest.raises(InvalidInput):
        answer(customer, clock, expenses=(yesterday,))
    answer(customer, clock, expenses=(PlannedExpense("Car", 500_000, TODAY),))  # today is fine


def test_ac8_other_customers_plan_is_forbidden(clock: FixedClock) -> None:
    plan = proposed_plan(clock)
    other = create_customer("bob", AC1_SERIES)
    with pytest.raises(PermissionDenied):
        get_owned_plan(other, plan.pk)
    with pytest.raises(Http404):
        get_owned_plan(other, plan.pk + 999)
    assert get_owned_plan(plan.customer, plan.pk) == plan


def test_pause_pauses_mandate_and_orders(clock: FixedClock) -> None:
    plan = proposed_plan(clock)
    accept_plan(plan, clock)
    pause_plan(plan, clock)
    plan.refresh_from_db()
    assert plan.status == Plan.Status.PAUSED
    assert Mandate.objects.get(plan=plan).status == Mandate.Status.PAUSED
    assert set(RecurringOrder.objects.values_list("status", flat=True)) == {"paused"}
    assert active_plan(plan.customer) == plan


def test_pausing_a_proposed_plan_is_a_conflict(clock: FixedClock) -> None:
    with pytest.raises(PlanConflict):
        pause_plan(proposed_plan(clock), clock)


def test_no_eligible_product_is_a_conflict(clock: FixedClock) -> None:
    Product.objects.update(active=False)
    customer = create_customer("anna", AC1_SERIES)
    answer(customer, clock)
    with pytest.raises(PlanConflict):
        propose_plan(customer, clock)


def test_time_machine_replays_the_plan(clock: FixedClock) -> None:
    result = time_machine(proposed_plan(clock), clock)
    assert len(result.months) == 6
    assert result.total_saved == 6 * 73_500
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/services/test_acceptance.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'plans.services'`.

- [ ] **Step 5: Implement the services**

`backend/plans/services.py`:

```python
"""Plan services: questionnaire, proposal, acceptance, rejection, editing, pausing.

The rule engine decides every number; these functions only load inputs, call `rules`,
store results and keep the audit log. Time always comes from the injected Clock.
"""

from collections.abc import Sequence

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Max
from django.http import Http404

from banking.models import Account, Product, Transaction
from core.clock import Clock
from plans.models import (
    ExpenseAnswer,
    LogEntry,
    Mandate,
    Plan,
    PlanItem,
    QuestionnaireAnswer,
    RecurringOrder,
    RuleConfig,
)
from rules.backtest import BacktestResult, backtest
from rules.confidence import Confidence, assess_confidence
from rules.mandate import PAUSE_CLAUSE
from rules.money import Huf
from rules.plan import (
    NoEligibleProduct,
    Outcome,
    PlanInputs,
    PlanItemDraft,
    Proposal,
    allocate,
    propose,
)
from rules.surplus import SurplusAnalysis, analyse_surplus
from rules.types import PlannedExpense, ProductInfo, Txn


class InvalidInput(Exception):
    """Well-formed input that breaks a business rule (HTTP 422)."""


class PlanConflict(Exception):
    """The action is not allowed in the current state (HTTP 409)."""


def log_event(
    customer: User,
    event: str,
    message: str,
    clock: Clock,
    *,
    plan: Plan | None = None,
    mandate_version: int | None = None,
    clause: int | None = None,
) -> LogEntry:
    return LogEntry.objects.create(
        customer=customer,
        plan=plan,
        event=event,
        message=message,
        mandate_version=mandate_version,
        clause=clause,
        created_at=clock.now(),
    )


def transactions_of(customer: User) -> list[Txn]:
    return [t.to_rule() for t in Transaction.objects.filter(account__customer=customer)]


def _active_products() -> list[ProductInfo]:
    return [p.to_rule() for p in Product.objects.filter(active=True)]


def _expenses(answer: QuestionnaireAnswer) -> list[PlannedExpense]:
    return [PlannedExpense(e.name, e.amount, e.due_on) for e in answer.expenses.all()]


def submit_questionnaire(
    customer: User,
    *,
    risk_score: int,
    existing_emergency_fund: Huf,
    expected_monthly_savings: Huf | None,
    planned_expenses: Sequence[PlannedExpense],
    clock: Clock,
) -> QuestionnaireAnswer:
    """Store the fixed questionnaire. Rejects past expense dates and non-positive amounts (AC8)."""
    today = clock.today()
    for expense in planned_expenses:
        if expense.amount <= 0:
            raise InvalidInput(f"The amount of '{expense.name}' must be positive.")
        if expense.due_on < today:
            raise InvalidInput(f"The due date of '{expense.name}' ({expense.due_on}) is in the past.")
    if existing_emergency_fund < 0:
        raise InvalidInput("The existing emergency fund cannot be negative.")
    if expected_monthly_savings is not None and expected_monthly_savings <= 0:
        raise InvalidInput("The expected monthly savings must be positive.")
    with transaction.atomic():
        answer = QuestionnaireAnswer.objects.create(
            customer=customer,
            risk_score=risk_score,
            existing_emergency_fund=existing_emergency_fund,
            expected_monthly_savings=expected_monthly_savings,
            submitted_at=clock.now(),
        )
        ExpenseAnswer.objects.bulk_create(
            [
                ExpenseAnswer(questionnaire=answer, name=e.name, amount=e.amount, due_on=e.due_on)
                for e in planned_expenses
            ]
        )
    return answer


def analyse(customer: User, clock: Clock) -> tuple[SurplusAnalysis, Confidence]:
    params = RuleConfig.load()
    analysis = analyse_surplus(transactions_of(customer), clock.today(), params)
    return analysis, assess_confidence(analysis.months_of_data, params)


def _save_items(plan: Plan, items: Sequence[PlanItemDraft]) -> None:
    PlanItem.objects.bulk_create(
        [
            PlanItem(
                plan=plan,
                position=position,
                kind=draft.kind.value,
                label=draft.label,
                product_id=draft.product.id,
                monthly_amount=draft.monthly_amount,
                target_amount=draft.target_amount,
            )
            for position, draft in enumerate(items)
        ]
    )


def propose_plan(customer: User, clock: Clock) -> tuple[Proposal, Plan | None]:
    """Run the rule engine on the latest questionnaire. Stores a Plan only for Outcome.PLAN."""
    answer = (
        QuestionnaireAnswer.objects.filter(customer=customer).order_by("-submitted_at", "-id").first()
    )
    if answer is None:
        raise PlanConflict("Please fill in the questionnaire first.")
    params = RuleConfig.load()
    inputs = PlanInputs(
        today=clock.today(),
        risk_score=answer.risk_score,
        existing_emergency_fund=answer.existing_emergency_fund,
        expected_monthly_savings=answer.expected_monthly_savings,
        planned_expenses=_expenses(answer),
        transactions=transactions_of(customer),
    )
    try:
        proposal = propose(inputs, _active_products(), params)
    except NoEligibleProduct as error:
        raise PlanConflict(str(error)) from error
    if proposal.outcome is not Outcome.PLAN:
        log_event(customer, proposal.outcome.value, "No plan was created.", clock)
        return proposal, None
    with transaction.atomic():
        plan = Plan.objects.create(
            customer=customer,
            questionnaire=answer,
            monthly_amount=proposal.monthly_amount,
            proposed_amount=proposal.monthly_amount,
            median_surplus=proposal.analysis.median_surplus,
            median_expenses=proposal.analysis.median_expenses,
            months_of_data=proposal.analysis.months_of_data,
            confidence=proposal.confidence.value,
            created_at=clock.now(),
        )
        _save_items(plan, proposal.items)
        log_event(
            customer,
            "plan_proposed",
            f"Plan {plan.pk} proposed: {proposal.monthly_amount} HUF a month.",
            clock,
            plan=plan,
        )
    return proposal, plan


def get_owned_plan(customer: User, plan_id: int) -> Plan:
    """Fetch by id, then check the owner: another customer's plan is 403, not 404 (AC8)."""
    plan = Plan.objects.filter(pk=plan_id).first()
    if plan is None:
        raise Http404("Plan not found.")
    if plan.customer_id != customer.pk:
        raise PermissionDenied("This plan belongs to another customer.")
    return plan


def accept_plan(plan: Plan, clock: Clock) -> list[RecurringOrder]:
    """Sign mandate version N+1 and create one recurring order per item, exactly once (AC7)."""
    with transaction.atomic():
        plan = Plan.objects.select_for_update().get(pk=plan.pk)
        if plan.status == Plan.Status.ACCEPTED:
            return list(RecurringOrder.objects.filter(plan_item__plan=plan).order_by("id"))
        if plan.status != Plan.Status.PROPOSED:
            raise PlanConflict(f"A {plan.status} plan cannot be accepted.")
        if Plan.objects.filter(customer_id=plan.customer_id, status=Plan.Status.ACCEPTED).exists():
            raise PlanConflict("Pause your active plan before accepting a new one.")
        items = list(plan.items.select_related("product"))
        latest = Mandate.objects.filter(customer_id=plan.customer_id).aggregate(v=Max("version"))
        version = (latest["v"] or 0) + 1
        mandate = Mandate.objects.create(
            customer_id=plan.customer_id,
            plan=plan,
            version=version,
            max_monthly_amount=plan.monthly_amount,
            min_balance=RuleConfig.load().min_balance,
            per_transfer_approval=plan.per_transfer_approval,
            signed_at=clock.now(),
        )
        mandate.products.set({item.product_id for item in items})
        orders = [
            RecurringOrder.objects.create(
                plan_item=item,
                mandate=mandate,
                product=item.product,
                monthly_amount=item.monthly_amount,
            )
            for item in items
        ]
        plan.status = Plan.Status.ACCEPTED
        plan.save(update_fields=["status"])
        log_event(
            plan.customer,
            "plan_accepted",
            f"Plan {plan.pk} accepted; mandate v{version} signed; {len(orders)} orders created.",
            clock,
            plan=plan,
            mandate_version=version,
        )
    return orders


def reject_plan(plan: Plan, clock: Clock) -> Plan:
    """A rejected plan never creates orders (AC7)."""
    if plan.status == Plan.Status.REJECTED:
        return plan
    if plan.status != Plan.Status.PROPOSED:
        raise PlanConflict(f"A {plan.status} plan cannot be rejected.")
    plan.status = Plan.Status.REJECTED
    plan.save(update_fields=["status"])
    log_event(plan.customer, "plan_rejected", f"Plan {plan.pk} rejected.", clock, plan=plan)
    return plan


def edit_amount(plan: Plan, monthly_amount: Huf, clock: Clock) -> Plan:
    """Lower the amount of a proposed plan and re-run the allocation. Nothing executes until
    the revised plan is accepted."""
    if plan.status != Plan.Status.PROPOSED:
        raise PlanConflict("Only a proposed plan can be edited.")
    if not 0 < monthly_amount <= plan.proposed_amount:
        raise InvalidInput(
            f"The monthly amount must be between 1 and {plan.proposed_amount} HUF."
        )
    answer = plan.questionnaire
    try:
        items = allocate(
            monthly_amount,
            median_expenses=plan.median_expenses,
            risk_score=answer.risk_score,
            existing_emergency_fund=answer.existing_emergency_fund,
            planned_expenses=_expenses(answer),
            today=clock.today(),
            products=_active_products(),
            params=RuleConfig.load(),
        )
    except NoEligibleProduct as error:
        raise PlanConflict(str(error)) from error
    with transaction.atomic():
        plan.items.all().delete()
        _save_items(plan, items)
        plan.monthly_amount = monthly_amount
        plan.save(update_fields=["monthly_amount"])
        log_event(
            plan.customer,
            "plan_edited",
            f"Plan {plan.pk} amount set to {monthly_amount} HUF a month.",
            clock,
            plan=plan,
        )
    return plan


def pause_plan(plan: Plan, clock: Clock) -> Plan:
    """Pause an accepted plan: its mandate and orders stop (mandate clause 4)."""
    if plan.status == Plan.Status.PAUSED:
        return plan
    if plan.status != Plan.Status.ACCEPTED:
        raise PlanConflict("Only an active plan can be paused.")
    with transaction.atomic():
        plan.status = Plan.Status.PAUSED
        plan.save(update_fields=["status"])
        mandate = Mandate.objects.get(plan=plan)
        mandate.status = Mandate.Status.PAUSED
        mandate.save(update_fields=["status"])
        RecurringOrder.objects.filter(mandate=mandate).update(status=RecurringOrder.Status.PAUSED)
        log_event(
            plan.customer,
            "plan_paused",
            f"Plan {plan.pk} paused.",
            clock,
            plan=plan,
            mandate_version=mandate.version,
            clause=PAUSE_CLAUSE,
        )
    return plan


def active_plan(customer: User) -> Plan | None:
    return (
        Plan.objects.filter(customer=customer, status__in=[Plan.Status.ACCEPTED, Plan.Status.PAUSED])
        .order_by("-created_at", "-id")
        .first()
    )


def time_machine(plan: Plan, clock: Clock) -> BacktestResult:
    """Replay the plan's monthly amount on the customer's own history (AC4)."""
    account = Account.objects.filter(customer_id=plan.customer_id).first()
    if account is None:
        raise PlanConflict("No account found for this customer.")
    return backtest(
        transactions_of(plan.customer),
        account.balance,
        plan.monthly_amount,
        clock.today(),
        RuleConfig.load(),
    )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/services -v`
Expected: all pass (test_acceptance: 18 including the 3 parametrized cases).

- [ ] **Step 7: Docs and check**

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Fixed explanation templates filled from rule results (`plans/explanations.py`).
- Plan services: questionnaire with past-date check (AC8), proposal (AC5, AC6), acceptance with versioned mandate and exactly-once recurring orders, rejection (AC7), amount edit, pause, ownership check (AC8).
```

Run: `make fmt && make check`. Expected: green.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(plans): proposal, acceptance and mandate services (AC5-AC8)`

---

### Task 12: Order execution through the mandate (AC6 approval, AC7 idempotency)

Deliverable: `run_monthly_orders()` executes each active order at most once per month, every transfer passes `check_action()`, low-confidence transfers wait for approval, and the log records mandate version and clause. `manage.py run_orders` runs it.

**Files:**
- Create: `backend/plans/execution.py`, `backend/plans/management/__init__.py`, `backend/plans/management/commands/__init__.py`, `backend/plans/management/commands/run_orders.py`, `backend/tests/services/test_execution.py`
- Modify: `docs/traceability.md` (AC6, AC7 → `passing`), `README.md`, `AGENTS.md` (section 4), `CHANGELOG.md`

**Interfaces:**
- Consumes: `check_action`, `TransferAction`, `APPROVAL_CLAUSE`, `AUTHORISING_CLAUSE`, `MIN_BALANCE_CLAUSE` (Task 8); models (Task 9); `log_event`, `PlanConflict`, `submit_questionnaire`, `propose_plan`, `accept_plan`, `pause_plan` (Task 11)
- Produces: `plans.execution.idempotency_key(order: RecurringOrder, period: date) -> str`, `run_monthly_orders(clock: Clock) -> list[Execution]`, `execute_order(order: RecurringOrder, period: date, clock: Clock, *, approved: bool = False) -> Execution`, `approve_execution(execution: Execution, clock: Clock) -> Execution`, `get_owned_execution(customer: User, execution_id: int) -> Execution` (404 / 403)

- [ ] **Step 1: Write the failing tests**

`backend/tests/services/test_execution.py`:

```python
from datetime import date
from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.management import call_command

from banking.models import Account, Product, Transaction
from core.clock import FixedClock
from plans.execution import approve_execution, get_owned_execution, run_monthly_orders
from plans.models import Execution, LogEntry, Plan
from plans.services import (
    PlanConflict,
    accept_plan,
    pause_plan,
    propose_plan,
    submit_questionnaire,
)
from rules.mandate import APPROVAL_CLAUSE, AUTHORISING_CLAUSE, MIN_BALANCE_CLAUSE
from rules.money import Huf
from tests.constants import AC1_SERIES
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db

DANI_SERIES = [50_000, 60_000, 55_000, 65_000]  # 4 months → low confidence, 40,250 HUF


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def accepted_plan(
    clock: FixedClock, username: str, surpluses: list[Huf], *, balance: Huf = 1_000_000
) -> Plan:
    customer = create_customer(username, surpluses, balance=balance)
    submit_questionnaire(
        customer,
        risk_score=3,
        existing_emergency_fund=750_000,  # full: one investment item
        expected_monthly_savings=None,
        planned_expenses=(),
        clock=clock,
    )
    _, plan = propose_plan(customer, clock)
    assert plan is not None
    accept_plan(plan, clock)
    return plan


def balance_of(customer: User) -> Huf:
    return Account.objects.get(customer=customer).balance


def test_execution_debits_account_and_logs_mandate_clause(clock: FixedClock) -> None:
    plan = accepted_plan(clock, "anna", AC1_SERIES)
    [execution] = run_monthly_orders(clock)
    assert execution.status == Execution.Status.EXECUTED
    assert (execution.mandate_version, execution.clause) == (1, AUTHORISING_CLAUSE)
    assert balance_of(plan.customer) == 1_000_000 - 73_500
    entry = LogEntry.objects.get(event="execution_executed")
    assert (entry.mandate_version, entry.clause) == (1, AUTHORISING_CLAUSE)
    transfer = Transaction.objects.filter(account__customer=plan.customer).last()
    assert transfer is not None
    assert (transfer.amount, transfer.own_transfer) == (-73_500, True)


def test_ac7_running_orders_twice_executes_once(clock: FixedClock) -> None:
    plan = accepted_plan(clock, "anna", AC1_SERIES)
    run_monthly_orders(clock)
    run_monthly_orders(clock)
    assert Execution.objects.count() == 1
    assert balance_of(plan.customer) == 1_000_000 - 73_500


def test_next_month_executes_again(clock: FixedClock) -> None:
    plan = accepted_plan(clock, "anna", AC1_SERIES)
    run_monthly_orders(clock)
    run_monthly_orders(FixedClock.on(date(2026, 11, 6)))
    assert Execution.objects.count() == 2
    assert balance_of(plan.customer) == 1_000_000 - 2 * 73_500


def test_transfer_below_minimum_balance_is_denied(clock: FixedClock) -> None:
    plan = accepted_plan(clock, "anna", AC1_SERIES, balance=120_000)
    [execution] = run_monthly_orders(clock)
    assert (execution.status, execution.clause) == (Execution.Status.DENIED, MIN_BALANCE_CLAUSE)
    assert balance_of(plan.customer) == 120_000


def test_ac6_low_confidence_transfer_waits_for_approval(clock: FixedClock) -> None:
    plan = accepted_plan(clock, "dani", DANI_SERIES)
    [execution] = run_monthly_orders(clock)
    assert execution.status == Execution.Status.AWAITING_APPROVAL
    assert execution.clause == APPROVAL_CLAUSE
    assert balance_of(plan.customer) == 1_000_000

    approved = approve_execution(execution, clock)
    assert approved.pk == execution.pk
    assert approved.status == Execution.Status.EXECUTED
    assert balance_of(plan.customer) == 1_000_000 - 40_250
    with pytest.raises(PlanConflict):
        approve_execution(approved, clock)
    run_monthly_orders(clock)
    assert Execution.objects.count() == 1


def test_paused_plan_executes_nothing(clock: FixedClock) -> None:
    plan = accepted_plan(clock, "anna", AC1_SERIES)
    pause_plan(plan, clock)
    assert run_monthly_orders(clock) == []
    assert Execution.objects.count() == 0


def test_other_customer_cannot_approve(clock: FixedClock) -> None:
    accepted_plan(clock, "dani", DANI_SERIES)
    [execution] = run_monthly_orders(clock)
    other = create_customer("bob", AC1_SERIES)
    with pytest.raises(PermissionDenied):
        get_owned_execution(other, execution.pk)


def test_run_orders_command(clock: FixedClock) -> None:
    accepted_plan(clock, "anna", AC1_SERIES)
    out = StringIO()
    call_command("run_orders", stdout=out)
    assert "1 orders processed: executed=1" in out.getvalue()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/services/test_execution.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'plans.execution'`.

- [ ] **Step 3: Implement execution**

`backend/plans/execution.py`:

```python
"""Monthly execution of recurring orders.

Every transfer passes rules.mandate.check_action() (golden rule 6). The Execution row and the
log entry store the mandate version and clause. A unique idempotency key per order and month
makes repeated runs harmless (AC7).
"""

from datetime import date

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Sum
from django.http import Http404

from banking.models import Account, Transaction
from core.clock import Clock
from plans.models import Execution, Mandate, RecurringOrder
from plans.services import PlanConflict, log_event
from rules.mandate import APPROVAL_CLAUSE, TransferAction, check_action
from rules.months import month_of


def idempotency_key(order: RecurringOrder, period: date) -> str:
    return f"order-{order.pk}-{period:%Y-%m}"


def run_monthly_orders(clock: Clock) -> list[Execution]:
    """Execute every active order once for the current calendar month."""
    period = month_of(clock.today())
    orders = RecurringOrder.objects.filter(status=RecurringOrder.Status.ACTIVE).order_by("id")
    return [execute_order(order, period, clock) for order in orders]


def execute_order(
    order: RecurringOrder, period: date, clock: Clock, *, approved: bool = False
) -> Execution:
    """Run one order for one month. Returns the existing execution if there is one, unless the
    customer is approving a transfer that was waiting for approval (AC6)."""
    key = idempotency_key(order, period)
    with transaction.atomic():
        existing = Execution.objects.select_for_update().filter(idempotency_key=key).first()
        approving = (
            approved
            and existing is not None
            and existing.status == Execution.Status.AWAITING_APPROVAL
        )
        if existing is not None and not approving:
            return existing
        mandate = Mandate.objects.select_related("customer", "plan").get(pk=order.mandate_id)
        account = Account.objects.select_for_update().get(customer_id=mandate.customer_id)
        already = (
            Execution.objects.filter(
                order__mandate=mandate, period=period, status=Execution.Status.EXECUTED
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        decision = check_action(
            mandate.terms(),
            TransferAction(
                product_id=order.product_id,
                amount=order.monthly_amount,
                balance_before=account.balance,
                transferred_this_month=already,
                approved_by_customer=approved,
            ),
        )
        if decision.allowed:
            status = Execution.Status.EXECUTED
            account.balance -= order.monthly_amount
            account.save(update_fields=["balance"])
            Transaction.objects.create(
                account=account,
                booked_on=clock.today(),
                amount=-order.monthly_amount,
                description=f"SaverAI order {order.pk}",
                own_transfer=True,  # savings transfer: excluded from future surplus analysis
            )
        elif decision.clause == APPROVAL_CLAUSE:
            status = Execution.Status.AWAITING_APPROVAL
        else:
            status = Execution.Status.DENIED
        execution, _ = Execution.objects.update_or_create(
            idempotency_key=key,
            defaults={
                "order": order,
                "period": period,
                "status": status,
                "amount": order.monthly_amount,
                "mandate_version": decision.mandate_version,
                "clause": decision.clause,
                "reason": decision.reason,
                "created_at": clock.now(),
            },
        )
        log_event(
            mandate.customer,
            f"execution_{status.value}",
            f"Order {order.pk}, {period:%Y-%m}: {decision.reason}",
            clock,
            plan=mandate.plan,
            mandate_version=decision.mandate_version,
            clause=decision.clause,
        )
    return execution


def get_owned_execution(customer: User, execution_id: int) -> Execution:
    """404 if missing, 403 if it belongs to another customer (AC8)."""
    execution = Execution.objects.select_related("order__mandate").filter(pk=execution_id).first()
    if execution is None:
        raise Http404("Transfer not found.")
    if execution.order.mandate.customer_id != customer.pk:
        raise PermissionDenied("This transfer belongs to another customer.")
    return execution


def approve_execution(execution: Execution, clock: Clock) -> Execution:
    """The customer approves one transfer of a plan without normal confidence (AC6)."""
    if execution.status != Execution.Status.AWAITING_APPROVAL:
        raise PlanConflict("Only a transfer that is waiting for approval can be approved.")
    return execute_order(execution.order, execution.period, clock, approved=True)
```

Create empty `backend/plans/management/__init__.py` and `backend/plans/management/commands/__init__.py`.

`backend/plans/management/commands/run_orders.py`:

```python
"""Execute this month's recurring orders. Idempotent: safe to run repeatedly (cron, demo).
Replaces APScheduler in M2 (ADR-0002)."""

from collections import Counter
from typing import Any

from django.core.management.base import BaseCommand

from core.clock import get_clock
from plans.execution import run_monthly_orders


class Command(BaseCommand):
    help = "Execute this month's recurring orders through the mandate check."

    def handle(self, *args: Any, **options: Any) -> None:
        executions = run_monthly_orders(get_clock())
        counts = Counter(str(e.status) for e in executions)
        summary = ", ".join(f"{status}={n}" for status, n in sorted(counts.items()))
        self.stdout.write(f"{len(executions)} orders processed: {summary}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/services/test_execution.py -v`
Expected: 8 passed.

- [ ] **Step 5: Docs and check**

In `docs/traceability.md` set AC6 and AC7 to `passing`.

In `README.md` under "Setup and run" add:

```
    cd backend && uv run python manage.py run_orders   # execute this month's orders (idempotent)
```

In `AGENTS.md` section 4, add after the Makefile code block: "Monthly orders: `cd backend && uv run python manage.py run_orders` (idempotent; APScheduler deferred, ADR-0002)."

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Monthly order execution through the mandate check with idempotency key per order and month (AC7); low-confidence transfers wait for customer approval (AC6); log stores mandate version and clause. `manage.py run_orders` (ADR-0002).
```

Run: `make fmt && make check`. Expected: green.

- [ ] **Step 6: Suggested commit (user commits)**

`feat(plans): idempotent order execution through mandate check (AC6, AC7)`

---

### Task 13: Customer API (AC5, AC6, AC8)

Deliverable: JSON endpoints for questionnaire, analysis, plan proposal, plan review, time machine, accept / reject / edit / pause, active plan and transfer approval. Strict integer money validation (422), ownership (403), state conflicts (409).

**Files:**
- Create: `backend/api/schemas.py`, `backend/api/routes.py`, `backend/tests/api/test_plans_api.py`
- Modify: `backend/api/api.py`, `docs/traceability.md` (AC5, AC8 → `passing`), `README.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `current_user` (Task 1), `get_clock` (Task 3), services (Task 11), execution (Task 12), explanations (Task 11)
- Produces (all under `/api`, session login required):

| Method | Path | Body | Response |
| --- | --- | --- | --- |
| POST | `/questionnaire` | `QuestionnaireIn` | 201 `{"id": int}` |
| GET | `/analysis` | — | `AnalysisOut` |
| POST | `/plans` | — | `ProposalOut` (`outcome`, `plan` or null, `explanations`) |
| GET | `/plans/active` | — | `PlanOut` or 404 |
| GET | `/plans/{id}` | — | `PlanOut` |
| PATCH | `/plans/{id}` | `{"monthly_amount": int}` | `PlanOut` |
| GET | `/plans/{id}/time-machine` | — | `TimeMachineOut` |
| POST | `/plans/{id}/accept` · `/reject` · `/pause` | — | `PlanOut` |
| GET | `/executions` | — | `list[ExecutionOut]` |
| POST | `/executions/{id}/approve` | — | `ExecutionOut` |

Errors: 401 not logged in, 403 another customer's data, 404 missing, 409 `PlanConflict`, 422 schema or `InvalidInput`. Error body: `{"detail": ...}`.

- [ ] **Step 1: Write the failing tests**

`backend/tests/api/test_plans_api.py`:

```python
from datetime import timedelta
from typing import Any

import pytest
from django.contrib.auth.models import User
from django.test import Client

from banking.models import Product
from core.clock import FixedClock
from plans.execution import run_monthly_orders
from plans.models import Plan, QuestionnaireAnswer, RecurringOrder
from rules.money import Huf
from tests.constants import AC1_SERIES, TODAY
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db

QUESTIONNAIRE: dict[str, Any] = {
    "risk_score": 3,
    "existing_emergency_fund": 750_000,
    "planned_expenses": [],
}


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def post(client: Client, url: str, body: dict[str, Any] | None = None) -> Any:
    return client.post(url, body or {}, content_type="application/json")


def patch(client: Client, url: str, body: dict[str, Any]) -> Any:
    return client.patch(url, body, content_type="application/json")


def login_as(client: Client, username: str, surpluses: list[Huf]) -> User:
    user = create_customer(username, surpluses)
    client.force_login(user)
    return user


def propose(client: Client, questionnaire: dict[str, Any] = QUESTIONNAIRE) -> dict[str, Any]:
    assert post(client, "/api/questionnaire", questionnaire).status_code == 201
    response = post(client, "/api/plans")
    assert response.status_code == 200
    result: dict[str, Any] = response.json()
    return result


def test_main_flow_questionnaire_to_accepted_plan(client: Client) -> None:
    login_as(client, "anna", AC1_SERIES)
    proposal = propose(client)
    analysis = client.get("/api/analysis").json()
    assert (analysis["monthly_amount"], analysis["confidence"]) == (73_500, "normal")
    assert proposal["outcome"] == "plan"
    assert "73,500 HUF" in proposal["explanations"][0]
    plan_id = proposal["plan"]["id"]

    machine = client.get(f"/api/plans/{plan_id}/time-machine").json()
    assert len(machine["months"]) == 6
    assert machine["total_saved"] == 6 * 73_500

    assert post(client, f"/api/plans/{plan_id}/accept").json()["status"] == "accepted"
    assert post(client, f"/api/plans/{plan_id}/accept").status_code == 200
    assert RecurringOrder.objects.count() == 1
    assert client.get("/api/plans/active").json()["id"] == plan_id
    assert post(client, f"/api/plans/{plan_id}/pause").json()["status"] == "paused"


def test_endpoints_require_login(client: Client) -> None:
    assert client.get("/api/analysis").status_code == 401
    assert post(client, "/api/plans").status_code == 401
    assert client.get("/api/plans/1").status_code == 401


def test_no_active_plan_is_404(client: Client) -> None:
    login_as(client, "anna", AC1_SERIES)
    assert client.get("/api/plans/active").status_code == 404


def test_ac5_no_surplus_creates_no_plan(client: Client) -> None:
    login_as(client, "bence", [-40_000] * 6)
    proposal = propose(client)
    assert proposal["outcome"] == "no_surplus"
    assert proposal["plan"] is None
    assert "no surplus" in proposal["explanations"][0]
    assert Plan.objects.count() == 0


def test_ac6_too_little_data_asks_for_expected_savings(client: Client) -> None:
    login_as(client, "csilla", [60_000, 70_000])
    first = propose(client)
    assert first["outcome"] == "needs_expected_savings"
    assert first["plan"] is None
    assert "expect to save" in first["explanations"][0]

    second = propose(client, {**QUESTIONNAIRE, "expected_monthly_savings": 40_000})
    assert second["outcome"] == "plan"
    assert second["plan"]["monthly_amount"] == 40_000
    assert second["plan"]["per_transfer_approval"] is True


def test_ac6_low_confidence_transfer_is_approved_through_api(
    client: Client, clock: FixedClock
) -> None:
    login_as(client, "dani", [50_000, 60_000, 55_000, 65_000])
    plan = propose(client)["plan"]
    assert (plan["confidence"], plan["per_transfer_approval"]) == ("low", True)
    post(client, f"/api/plans/{plan['id']}/accept")
    run_monthly_orders(clock)
    [pending] = client.get("/api/executions").json()
    assert (pending["status"], pending["clause"]) == ("awaiting_approval", 3)
    approved = post(client, f"/api/executions/{pending['id']}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "executed"
    assert post(client, f"/api/executions/{pending['id']}/approve").status_code == 409


@pytest.mark.parametrize(
    "change",
    [
        {"existing_emergency_fund": -1},
        {"expected_monthly_savings": -5},
        {"planned_expenses": [{"name": "Car", "amount": -500_000, "due_on": "2027-08-15"}]},
    ],
)
def test_ac8_negative_amount_is_rejected(client: Client, change: dict[str, Any]) -> None:
    login_as(client, "anna", AC1_SERIES)
    assert post(client, "/api/questionnaire", {**QUESTIONNAIRE, **change}).status_code == 422
    assert QuestionnaireAnswer.objects.count() == 0


@pytest.mark.parametrize("value", [100.0, 100.5, "100", True])
def test_ac8_non_integer_amount_is_rejected(client: Client, value: object) -> None:
    login_as(client, "anna", AC1_SERIES)
    body = {**QUESTIONNAIRE, "existing_emergency_fund": value}
    assert post(client, "/api/questionnaire", body).status_code == 422


def test_out_of_range_risk_score_is_rejected(client: Client) -> None:
    login_as(client, "anna", AC1_SERIES)
    assert post(client, "/api/questionnaire", {**QUESTIONNAIRE, "risk_score": 6}).status_code == 422


def test_ac8_past_expense_date_is_rejected(client: Client) -> None:
    login_as(client, "anna", AC1_SERIES)
    expense = {"name": "Car", "amount": 500_000, "due_on": (TODAY - timedelta(days=1)).isoformat()}
    response = post(client, "/api/questionnaire", {**QUESTIONNAIRE, "planned_expenses": [expense]})
    assert response.status_code == 422
    assert "past" in response.json()["detail"]
    expense["due_on"] = TODAY.isoformat()
    assert post(client, "/api/questionnaire", {**QUESTIONNAIRE, "planned_expenses": [expense]}).status_code == 201


def test_ac8_negative_edit_amount_is_rejected(client: Client) -> None:
    login_as(client, "anna", AC1_SERIES)
    plan_id = propose(client)["plan"]["id"]
    assert patch(client, f"/api/plans/{plan_id}", {"monthly_amount": -5}).status_code == 422
    assert patch(client, f"/api/plans/{plan_id}", {"monthly_amount": 80_000}).status_code == 422
    edited = patch(client, f"/api/plans/{plan_id}", {"monthly_amount": 50_000})
    assert edited.status_code == 200
    assert (edited.json()["monthly_amount"], edited.json()["status"]) == (50_000, "proposed")


def test_ac8_other_customer_cannot_view_or_accept_plan(client: Client) -> None:
    login_as(client, "anna", AC1_SERIES)
    plan_id = propose(client)["plan"]["id"]
    client.logout()
    login_as(client, "bob", AC1_SERIES)
    assert client.get(f"/api/plans/{plan_id}").status_code == 403
    assert post(client, f"/api/plans/{plan_id}/accept").status_code == 403
    assert client.get(f"/api/plans/{plan_id}/time-machine").status_code == 403
    assert patch(client, f"/api/plans/{plan_id}", {"monthly_amount": 1_000}).status_code == 403
    assert client.get(f"/api/plans/{plan_id + 999}").status_code == 404
    assert RecurringOrder.objects.count() == 0


def test_accepting_a_rejected_plan_is_a_conflict(client: Client) -> None:
    login_as(client, "anna", AC1_SERIES)
    plan_id = propose(client)["plan"]["id"]
    assert post(client, f"/api/plans/{plan_id}/reject").json()["status"] == "rejected"
    assert post(client, f"/api/plans/{plan_id}/accept").status_code == 409
    assert RecurringOrder.objects.count() == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/api/test_plans_api.py`
Expected: FAIL — every request returns 404 (routes do not exist yet).

- [ ] **Step 3: Implement schemas**

`backend/api/schemas.py`:

```python
"""Request and response schemas. Money and scores are strict ints: floats, strings and booleans
are rejected with 422 (golden rule 3, AC8). Past-date checks need the Clock, so they live in
plans.services.submit_questionnaire."""

from datetime import date
from typing import Annotated

from ninja import Schema
from pydantic import Field

PositiveHuf = Annotated[int, Field(strict=True, gt=0)]
NonNegativeHuf = Annotated[int, Field(strict=True, ge=0)]
RiskScore = Annotated[int, Field(strict=True, ge=1, le=5)]


class ExpenseIn(Schema):
    name: str = Field(min_length=1, max_length=100)
    amount: PositiveHuf
    due_on: date


class QuestionnaireIn(Schema):
    risk_score: RiskScore
    existing_emergency_fund: NonNegativeHuf
    expected_monthly_savings: PositiveHuf | None = None
    planned_expenses: list[ExpenseIn] = Field(default_factory=list, max_length=10)


class AmountIn(Schema):
    monthly_amount: PositiveHuf


class IdOut(Schema):
    id: int


class MonthOut(Schema):
    month: date
    income: int
    expenses: int
    surplus: int


class AnalysisOut(Schema):
    months_of_data: int
    confidence: str
    median_surplus: int | None
    median_expenses: int
    monthly_amount: int | None
    months: list[MonthOut]


class ProductOut(Schema):
    id: int
    name: str
    risk_level: int
    liquid: bool


class PlanItemOut(Schema):
    kind: str
    label: str
    product: ProductOut
    monthly_amount: int
    target_amount: int | None


class PlanOut(Schema):
    id: int
    status: str
    monthly_amount: int
    proposed_amount: int
    confidence: str
    per_transfer_approval: bool
    items: list[PlanItemOut]
    explanations: list[str]


class ProposalOut(Schema):
    outcome: str
    plan: PlanOut | None
    explanations: list[str]


class BacktestMonthOut(Schema):
    month: date
    balance_before_transfer: int
    transfer: int
    skipped: bool
    balance_after: int
    saved_to_date: int
    note: str | None


class TimeMachineOut(Schema):
    total_saved: int
    skipped_months: list[date]
    months: list[BacktestMonthOut]


class ExecutionOut(Schema):
    id: int
    period: date
    status: str
    amount: int
    mandate_version: int
    clause: int
    reason: str
```

- [ ] **Step 4: Implement routes**

`backend/api/routes.py`:

```python
"""Customer endpoints. Plans and transfers are always loaded through the ownership checks in
plans.services / plans.execution, so another customer's data gives 403 (AC8)."""

from django.http import Http404, HttpRequest
from ninja import Router

from api.auth import current_user
from api.schemas import (
    AmountIn,
    AnalysisOut,
    BacktestMonthOut,
    ExecutionOut,
    IdOut,
    MonthOut,
    PlanItemOut,
    PlanOut,
    ProductOut,
    ProposalOut,
    QuestionnaireIn,
    TimeMachineOut,
)
from core.clock import get_clock
from plans import execution as executions
from plans import explanations, services
from plans.models import Execution, Plan, RuleConfig
from rules.confidence import Confidence
from rules.plan import Outcome, Proposal
from rules.types import PlannedExpense

router = Router(tags=["customer"])


def plan_out(plan: Plan) -> PlanOut:
    params = RuleConfig.load()
    items = [
        PlanItemOut(
            kind=item.kind,
            label=item.label,
            product=ProductOut(
                id=item.product.pk,
                name=item.product.name,
                risk_level=item.product.risk_level,
                liquid=item.product.liquid,
            ),
            monthly_amount=item.monthly_amount,
            target_amount=item.target_amount,
        )
        for item in plan.items.select_related("product")
    ]
    return PlanOut(
        id=plan.pk,
        status=plan.status,
        monthly_amount=plan.monthly_amount,
        proposed_amount=plan.proposed_amount,
        confidence=plan.confidence,
        per_transfer_approval=plan.per_transfer_approval,
        items=items,
        explanations=explanations.plan_summary(
            amount=plan.monthly_amount,
            median_surplus=plan.median_surplus,
            percent=params.monthly_share_percent,
            months_of_data=plan.months_of_data,
            confidence=Confidence(plan.confidence),
        ),
    )


def no_plan_explanations(proposal: Proposal) -> list[str]:
    analysis = proposal.analysis
    if proposal.outcome is Outcome.NO_SURPLUS:
        return [explanations.no_surplus(len(analysis.flows), analysis.median_surplus or 0)]
    required = RuleConfig.load().min_months_for_estimate
    return [explanations.needs_expected_savings(analysis.months_of_data, required)]


def execution_out(execution: Execution) -> ExecutionOut:
    return ExecutionOut(
        id=execution.pk,
        period=execution.period,
        status=execution.status,
        amount=execution.amount,
        mandate_version=execution.mandate_version,
        clause=execution.clause,
        reason=execution.reason,
    )


def owned_plan(request: HttpRequest, plan_id: int) -> Plan:
    return services.get_owned_plan(current_user(request), plan_id)


@router.post("/questionnaire", response={201: IdOut})
def submit_questionnaire(request: HttpRequest, payload: QuestionnaireIn) -> tuple[int, IdOut]:
    answer = services.submit_questionnaire(
        current_user(request),
        risk_score=payload.risk_score,
        existing_emergency_fund=payload.existing_emergency_fund,
        expected_monthly_savings=payload.expected_monthly_savings,
        planned_expenses=[
            PlannedExpense(e.name, e.amount, e.due_on) for e in payload.planned_expenses
        ],
        clock=get_clock(),
    )
    return 201, IdOut(id=answer.pk)


@router.get("/analysis", response=AnalysisOut)
def analysis(request: HttpRequest) -> AnalysisOut:
    result, confidence = services.analyse(current_user(request), get_clock())
    return AnalysisOut(
        months_of_data=result.months_of_data,
        confidence=confidence.value,
        median_surplus=result.median_surplus,
        median_expenses=result.median_expenses,
        monthly_amount=result.monthly_amount,
        months=[
            MonthOut(month=f.month, income=f.income, expenses=f.expenses, surplus=f.surplus)
            for f in result.flows
        ],
    )


@router.post("/plans", response=ProposalOut)
def propose_plan(request: HttpRequest) -> ProposalOut:
    proposal, plan = services.propose_plan(current_user(request), get_clock())
    if plan is None:
        return ProposalOut(
            outcome=proposal.outcome.value, plan=None, explanations=no_plan_explanations(proposal)
        )
    out = plan_out(plan)
    return ProposalOut(outcome=proposal.outcome.value, plan=out, explanations=out.explanations)


@router.get("/plans/active", response=PlanOut)
def get_active_plan(request: HttpRequest) -> PlanOut:
    plan = services.active_plan(current_user(request))
    if plan is None:
        raise Http404("No active plan.")
    return plan_out(plan)


@router.get("/plans/{plan_id}", response=PlanOut)
def get_plan(request: HttpRequest, plan_id: int) -> PlanOut:
    return plan_out(owned_plan(request, plan_id))


@router.patch("/plans/{plan_id}", response=PlanOut)
def edit_plan(request: HttpRequest, plan_id: int, payload: AmountIn) -> PlanOut:
    plan = services.edit_amount(owned_plan(request, plan_id), payload.monthly_amount, get_clock())
    return plan_out(plan)


@router.get("/plans/{plan_id}/time-machine", response=TimeMachineOut)
def time_machine(request: HttpRequest, plan_id: int) -> TimeMachineOut:
    result = services.time_machine(owned_plan(request, plan_id), get_clock())
    minimum = RuleConfig.load().min_balance
    return TimeMachineOut(
        total_saved=result.total_saved,
        skipped_months=list(result.skipped_months),
        months=[
            BacktestMonthOut(
                month=m.month,
                balance_before_transfer=m.balance_before_transfer,
                transfer=m.transfer,
                skipped=m.skipped,
                balance_after=m.balance_after,
                saved_to_date=m.saved_to_date,
                note=explanations.skipped_month(m.month, minimum) if m.skipped else None,
            )
            for m in result.months
        ],
    )


@router.post("/plans/{plan_id}/accept", response=PlanOut)
def accept_plan(request: HttpRequest, plan_id: int) -> PlanOut:
    plan = owned_plan(request, plan_id)
    services.accept_plan(plan, get_clock())
    plan.refresh_from_db()
    return plan_out(plan)


@router.post("/plans/{plan_id}/reject", response=PlanOut)
def reject_plan(request: HttpRequest, plan_id: int) -> PlanOut:
    return plan_out(services.reject_plan(owned_plan(request, plan_id), get_clock()))


@router.post("/plans/{plan_id}/pause", response=PlanOut)
def pause_plan(request: HttpRequest, plan_id: int) -> PlanOut:
    return plan_out(services.pause_plan(owned_plan(request, plan_id), get_clock()))


@router.get("/executions", response=list[ExecutionOut])
def list_executions(request: HttpRequest) -> list[ExecutionOut]:
    rows = Execution.objects.filter(order__mandate__customer=current_user(request)).order_by(
        "-period", "id"
    )
    return [execution_out(e) for e in rows]


@router.post("/executions/{execution_id}/approve", response=ExecutionOut)
def approve_execution(request: HttpRequest, execution_id: int) -> ExecutionOut:
    execution = executions.get_owned_execution(current_user(request), execution_id)
    return execution_out(executions.approve_execution(execution, get_clock()))
```

`/plans/active` is declared before `/plans/{plan_id}` on purpose: route order decides the match.

- [ ] **Step 5: Register the router and error mapping**

Replace `backend/api/api.py` with:

```python
"""The Django Ninja API. Every endpoint needs a session login unless it sets auth=None.
Service exceptions map to HTTP: PermissionDenied 403, PlanConflict 409, InvalidInput 422."""

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI
from ninja.security import django_auth

from api.auth import router as auth_router
from api.routes import router as customer_router
from plans.services import InvalidInput, PlanConflict

api = NinjaAPI(title="SaverAI", auth=django_auth)
api.add_router("/auth", auth_router)
api.add_router("/", customer_router)


@api.exception_handler(PermissionDenied)
def forbidden(request: HttpRequest, exc: PermissionDenied) -> HttpResponse:
    return api.create_response(request, {"detail": str(exc) or "Forbidden."}, status=403)


@api.exception_handler(PlanConflict)
def conflict(request: HttpRequest, exc: PlanConflict) -> HttpResponse:
    return api.create_response(request, {"detail": str(exc)}, status=409)


@api.exception_handler(InvalidInput)
def invalid_input(request: HttpRequest, exc: InvalidInput) -> HttpResponse:
    return api.create_response(request, {"detail": str(exc)}, status=422)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/api -v`
Expected: all pass (test_plans_api: 18 including parametrized cases; test_auth: 6). If every customer route is 404, check the router prefix: `api.add_router("/", ...)` plus paths starting with `/` must yield `/api/questionnaire`; print `[str(p.pattern) for p in api.urls[0]]` to see the real paths and fix the prefix, not the tests.

- [ ] **Step 7: Docs and check**

In `docs/traceability.md` set AC5 and AC8 to `passing`. All eight rows should now be `passing`.

Add to `README.md`:

```markdown
## API
Interactive docs at http://localhost:8000/api/docs after `make dev`. Log in with
`POST /api/auth/login`; customer endpoints: questionnaire, analysis, plans (propose, review,
edit, accept, reject, pause, time machine), executions (list, approve).
```

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Customer API: questionnaire, spending analysis, plan proposal and review, time machine, accept / reject / edit / pause, active plan, transfer approval. Strict integer money validation and past-date check return 422; another customer's plan returns 403 (AC5, AC6, AC8).
```

Run: `make fmt && make check`. Expected: green.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(api): customer plan endpoints with validation and ownership checks (AC5, AC6, AC8)`

---

### Task 14: Manual checks, AI usage draft, final verification

Deliverable: reproducible manual checks, a drafted AI usage entry for the human author to complete, and a clean `make check` from a fresh database.

**Files:**
- Create: `docs/manual-checks.md`
- Modify: `docs/ai-usage.md`, `docs/traceability.md`, `CHANGELOG.md`

- [ ] **Step 1: Write `docs/manual-checks.md`**

````markdown
# Manual checks

Reproducible checks for behaviour that is easiest to see in the running app.
Setup for every check: `make setup && make seed && make dev` with `SAVERAI_FIXED_DATE=2026-10-06`
in `.env` (so the expected numbers match). Passwords: `SEED_PASSWORD` from `.env`.

## RuleConfig change (defence rehearsal)
1. Open http://localhost:8000/admin/, log in as `admin`.
2. Rule configuration → set "Monthly share percent" to 60 → Save.
3. Log in as `anna` through `POST /api/auth/login` (or the API docs page) and call `GET /api/analysis`.
Expected: `monthly_amount` is 63000 (60 % of the 105,000 median). Set it back to 70 → 73500.

## AC4 — time machine skipped month
1. Log in as `anna`, `POST /api/questionnaire` with
   `{"risk_score": 3, "existing_emergency_fund": 750000, "planned_expenses": []}`, then `POST /api/plans`.
2. In Django admin, lower anna's account balance to 300000.
3. `GET /api/plans/{id}/time-machine`.
Expected: some months have `"skipped": true`, `transfer` 0 and a `note` saying the transfer would
have left less than 100,000 HUF.

## Product catalogue (Admin role)
1. In Django admin, add a product with risk level 6.
Expected: the form rejects it (risk level must be 1–5).
````

- [ ] **Step 2: Draft the AI usage entry**

Append to `docs/ai-usage.md` (the human author verifies and completes the decision fields):

```markdown
### Case 2 — Backend implementation plan (DRAFT, author to complete)
- Phase: design
- Tool and model: Claude Code, Claude Opus 5.5 (superpowers "writing-plans" skill)
- Problem: turn AC1–AC8 and the M2 task list into an ordered, test-first backend plan.
- Context given and key instruction: `docs/specification.md`, `docs/tasks.md`, `AGENTS.md`;
  "Create the backend implementation plan based on the specification and the todos, don't commit anything".
- Essence of the AI suggestion: 14 TDD tasks; spec-silent edge cases decided in ADR-0002
  (median ≤ 0 → no plan, `low_risk_max` parameter, strict-priority allocation, recurring orders in
  the `plans` app, `run_orders` command instead of APScheduler).
- Decision (accepted / modified / rejected) and technical reasons: TODO author
- Verification: `make check` after every task; `docs/traceability.md`.
- Limitations of this verification: the plan was written before any code ran; framework details
  (Ninja auth, mypy with django-stubs) were first verified in Task 1.
```

- [ ] **Step 3: Final verification from a clean database**

Run:

```bash
rm -f backend/db.sqlite3
make migrate
make seed        # uses SEED_PASSWORD from .env (the Makefile's .env values override shell variables)
make check
cd backend && uv run python manage.py check
```

Expected: migrations apply; `Seeded 5 products and 4 personas.`; lint clean, all tests pass, `docs-check: OK`; `System check identified no issues`.

Then: `cd backend && uv run python manage.py makemigrations --check --dry-run`
Expected: `No changes detected` (models and migrations agree).

- [ ] **Step 4: Traceability and changelog**

In `docs/traceability.md`, confirm all eight rows are `passing` and add one line under the table:

```markdown
Last full run: `make check` on <date> — <N> passed (fill in from the Step 3 output).
```

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Manual checks (`docs/manual-checks.md`) and AI usage Case 2 draft.
```

Run: `make check`. Expected: green.

- [ ] **Step 5: Suggested commit (user commits)**

`docs: manual checks, ai usage draft and final traceability`

After the user commits: M2 also needs the frontend plan, the Playwright e2e test, and the `v1.0-first-version` tag. Those are out of scope for this plan.
