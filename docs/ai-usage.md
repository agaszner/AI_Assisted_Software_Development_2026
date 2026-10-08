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


### Case 2 — Idempotent plan acceptance and order execution (AC7)
- Phase: design (before Tasks 9, 11 and 12 of the backend plan: data model, acceptance, execution)
- Tool and model: Claude Code; Opus 5.5 
- Problem: AC7 requires that accepting a plan twice creates its recurring orders only once, that a
  rejected plan creates none, and that a monthly run never executes the same order twice. Double
  clicks and overlapping scheduler runs make duplicates a realistic risk.
- Context given and key instruction: `docs/specification.md` (AC7, AC8), `AGENTS.md` golden rules
  5–7 (injected clock, mandate check, idempotency key on `Execution`), SQLite as the database.
  Instruction: how to prevent duplicates for AC7.
- Essence of the AI suggestion: two separate guards.
  1. Plan acceptance: inside `transaction.atomic()`, lock the plan with `select_for_update()`,
     create orders only if the status is still `PROPOSED`.
  2. Order execution: a unique `Execution.idempotency_key` built as `"{order_id}:{YYYY-MM}"` from
     `clock.today()`; create the row inside `atomic()` and treat `IntegrityError` as "already ran".
- Decision: **modified.**
  - Guard 2 accepted: a database unique constraint stays correct under a race; an app-level
    "already exists?" check does not.
  - Guard 1 replaced with a conditional update,
    `Plan.objects.filter(pk=…, status=PROPOSED).update(status=ACCEPTED)`, creating orders only when
    it updated one row. `select_for_update()` has no effect on SQLite, so two concurrent accepts
    could both read `PROPOSED`; the conditional update is atomic on any database.
  - The key uses the scheduled period being executed, not `clock.today()`. Otherwise a late run
    (the September order executed on 2 October) gets the October key and skips or duplicates a month.
  - Added what the suggestion left out: `rules.mandate.check_action()` before every execution, with
    the mandate version and clause logged (golden rule 6), and an ownership check returning 403 for
    another customer's plan instead of the 404 that `.get(customer=user)` would give (AC8).
