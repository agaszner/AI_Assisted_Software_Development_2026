# AI usage

How AI tools are used to **develop** SaverAI. The running application contains no AI service
(AGENTS.md golden rule 1). Entry format: AGENTS.md section 8.4.

## Decision cases

### Case 1 — Backend framework: Django instead of FastAPI
- Phase: design (backend implementation plan)
- Tool and model: Claude Code while writing the backend implementation plan; Opus 5.5 model.
- Problem: the backend needs a JSON API for the React frontend, a database with migrations, login
  with two roles (`customer`, `admin`) and an admin UI for products and rule parameters. A framework
  had to be chosen before the plan could fix files, commands and tests.
- Context given and key instruction: `docs/specification.md` (AC1–AC8), `AGENTS.md` (golden rules,
  "Admin" role, data-model and change-request rules) and `docs/tasks.md`. Instruction: write a
  task-by-task backend implementation plan.
- Essence of the AI suggestion: build the backend on **FastAPI**: a lightweight async API with
  Pydantic validation.
- Decision: **rejected; Django 5 + Django Ninja chosen instead.** Reasons:
  - I know Django better than FastAPI.
  - Django ships the parts the specification needs: ORM and migrations (the change request needs a
    new migration and a data-preservation test), authentication with groups for the two roles, and
    Django admin for the Admin role (products, `RuleConfig`). With FastAPI each of these is a
    separate dependency (e.g. SQLAlchemy, Alembic, an auth library, an admin package), more code to
    write, and more code to explain.
  - Django Ninja keeps the useful part of the suggestion: Pydantic schemas with FastAPI-style
    validation, so invalid input returns 422 (AC8).
  - Async gives no benefit here: SQLite, a few users, no slow external calls.
- Verification: the decision is recorded in `docs/decisions/0001-tech-stack.md` (accepted) and
  `AGENTS.md` section 3. The Task 1 skeleton is built on it: Django admin, session login and roles
  run, and `backend/tests/api/test_auth.py` passes (6 tests) in `make check`.

