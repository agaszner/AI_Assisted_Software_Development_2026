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

### Case 3 — UI target: mobile first rejected, responsive web chosen (DRAFT — author to verify)
- Phase: design
- Tool and model: Opus 5.5 the tool and model that suggested mobile first. The web redesign was
  made with Claude Opus 5.5 and the Figma MCP server.
- Problem: the specification described a "React mobile banking UI". The first Figma design
  (https://www.figma.com/design/BqX09Awt7irGNkgUDShfsa) targeted 1440 px desktop web with a six-item top
  navigation. The UI target had to be fixed before the React frontend is built. UI did not look modern.
- Context given and key instruction: `docs/specification.md`, `AGENTS.md`, `backend/plans/explanations.py`,
  the seed personas and a review of the first design.
- Essence of the AI suggestion: design the UI mobile first: phone-sized screens, a bottom `TabBar` and
  slide-up sheets for confirmations, in line with the "mobile banking UI" wording of the specification.
- Decision: **rejected; responsive web chosen.**
  Reasons (author to verify and complete):
  - The app is demonstrated and tested in a desktop browser (`make dev`, Playwright e2e).
  - The wide screen keeps the decision visible. On Plan review and Mandate, a summary panel stays in
    place on the right while scrolling: amount, confidence badge, time machine summary and the single
    main button.
  - Web-banking patterns fit the content better: a left sidebar (Home · Savings plan · Activity ·
    Profile) as on Wise and Revolut web, a focused checkout-style plan flow (Step N of 4, Back,
    Save & exit), a centered "Confirm with password" modal (simulated strong customer authentication)
    and the execution log as a table with an expandable audit row.
  - Small screens are still covered: there is no separate mobile design, but the two-column screens
    stack at about 768 px and 375 px, and the 44 px minimum target is kept.
  - The new web was better for UX.
- Verification: new file https://www.figma.com/design/QUT5rnXj1U6BYjty7YH5uS. . Texts come from
  `backend/plans/explanations.py` and the `InvalidInput` messages in `backend/plans/services.py`. The plan
  amounts (73,500 HUF split 30,000 / 30,000 / 13,500; 40,250 HUF for dani; -40,000 HUF for bence; 2 months
  for csilla) were produced by running `rules.plan.propose` on the seed personas with today 2026-10-08 and
  risk score 2; for anna also an existing emergency fund of 720,000 HUF and a planned expense "New laptop",
  300,000 HUF, due 2027-08-01. `docs/specification.md`,
  `docs/SaverAI_BIA823.docx`, `AGENTS.md` section 5 and `docs/tasks.md` were updated to match.
- Limitations of this verification: visual review only, no usability test. The time machine figures
  (735,000 HUF, 2 skipped months over 12 months) are an illustrative 12-month scenario. Seed persona anna
  has only 6 months of data, for which the engine gives 441,000 HUF and no skipped month. Order IDs in
  idempotency keys are illustrative. The sticky summary panel is annotated in the file, not prototyped.
