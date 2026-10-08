# SaverAI — Task list

Ordered by milestone. Each task names the AC it serves. Exact milestone dates are published in Moodle.
Sources: `docs/Homework_requirements_EN.pdf`, `docs/specification.md`, `AGENTS.md`.

## M1 — Specification (deadline: end of week 6)

- [X] Upload specification text to Moodle "Homework specification".
- [X] Commit `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` symlinks and `docs/ai-usage.md`.
- [X] Create a **public** GitHub repository and push.

## M2 — First working version (deadline: end of week 10)

### Project skeleton
- [ ] `Makefile` with targets from AGENTS.md section 4 (`setup`, `migrate`, `seed`, `dev`, `test`, `test-fe`, `e2e`, `lint`, `docs-check`, `check`).
- [X] `.env.example`; keep `.env` in `.gitignore`.
- [X] Django 5 + Django Ninja project in `backend/` (`config/`, `core/`, `banking/`, `plans/`, `api/`).
- [ ] React + TypeScript (strict) + Vite + Tailwind in `frontend/`.
- [ ] Tooling config: ruff, mypy, pytest, pytest-django, Hypothesis, eslint, prettier, Vitest.
- [ ] `docker-compose.yml` (optional; Makefile is enough for the defence).
- [X] ADR-0001: tech stack choice (`docs/decisions/0001-tech-stack.md`).

### Core (`backend/core/`, `backend/rules/` — pure, no Django)
- [X] `core/clock.py`: `Clock` protocol, system clock, fixed clock for tests.
- [X] `rules/money.py`: `Huf = int`, single rounding rule.
- [X] `rules/defaults.py`: 70 %, 3 months, 6 months, 12 months, 100,000 HUF.
- [X] `rules/surplus.py`: monthly surplus per calendar month, ignore own-account transfers, median of last 6 months, 70 % monthly amount. **AC1, AC5**
- [X] `rules/confidence.py`: < 3 months = no estimate; 3–5 months = low confidence + per-transfer approval. **AC6**
- [X] `rules/plan.py`: priority emergency fund (3× median expenses) → planned expenses → long-term investment; ≤ 12 months = low-risk liquid only; no product above customer risk score. **AC2, AC3**
- [X] `rules/backtest.py`: replay plan on 12 months of transactions, flag months where the transfer would break the 100,000 HUF minimum. **AC4** (dual-implementation feature, see M3)
- [X] `rules/mandate.py`: mandate schema + `check_action()` returning allowed/denied with version and clause.

### Data model and services
- [ ] `banking` models: Account, Transaction, Product (risk 1–5, minimum horizon, liquid flag), Order.
- [ ] `plans` models: QuestionnaireAnswer, Plan (status: proposed / accepted / rejected / paused), PlanItem, Mandate (versioned), Execution (idempotency key, unique constraint), LogEntry.
- [ ] `RuleConfig` model with defaults from `rules/defaults.py`, editable in Django admin.
- [ ] Django admin for products and `RuleConfig` (Admin role).
- [ ] Plan acceptance service: creates recurring orders exactly once; rejected plan creates none. **AC7**
- [ ] Order execution service: every execution passes `check_action()`; log records mandate version and clause.
- [ ] `plans/explanations.py`: fixed templates filled only from rule results (no surplus, too little data, low confidence, skipped month).
- [ ] Synthetic data generator + `make seed`: personas covering AC1 (the 100k/120k/80k/110k/90k/300k series), AC2 (no emergency fund), AC5 (negative surplus), AC6 (2 months and 4 months of data).

### API (`backend/api/`)
- [X] Auth: login/logout, roles `customer` and `admin`.
- [ ] Endpoints: questionnaire submit, spending analysis, plan proposal, time machine, accept / reject / edit amount, pause, active plan.
- [ ] Ninja schemas validate input: negative amount and past expense date return 422. **AC8**
- [ ] Ownership check: another customer's plan returns 403 on view and accept. **AC8**

### Frontend (`frontend/src/screens/`)
- [ ] Theme tokens in `src/theme/` (from Figma variables if available).
- [ ] Shared components: Button, TransactionRow, TabBar (44 px touch targets, accessible labels).
- [ ] Screens: login, home, questionnaire, plan review (with confidence level), time machine (chart with skipped months), mandate, active plan (pause).
- [ ] Empty/explanation states: no surplus (AC5), too little data asks for expected monthly savings (AC6).

### Tests (names `test_acN_<behaviour>`)
- [X] AC1 normal: `test_ac1_median_surplus_gives_73500`.
- [X] AC2 normal: emergency fund comes first.
- [X] AC3 edge: 10-month expense → liquid low-risk only; risk score 2 → nothing above 2.
- [X] AC4 edge: skipped month flagged when balance would drop below 100,000 HUF.
- [ ] AC5 edge: negative median → no plan + message.
- [X] AC6 edge: 2 months → no estimate; 4 months → low confidence.
- [ ] AC7 regression-style: accept twice → one set of orders; reject → none.
- [ ] AC8 invalid + unauthorised: 422 cases, 403 case.
- [X] Hypothesis property: balance never below mandate minimum for any transaction sequence.
- [ ] One Playwright e2e of the main workflow (questionnaire → plan → time machine → accept).

### Documentation
- [ ] `README.md`: setup, run, test commands, link to `docs/ai-usage.md`.
- [X] `docs/traceability.md`: one row per AC, verification method, test path, status.
- [ ] `docs/manual-checks.md`: reproducible steps for UI-only checks.
- [ ] `docs/architecture.md`: components and data model.
- [X] `CHANGELOG.md` (Keep a Changelog).
- [X] `make docs-check` script (AC ↔ traceability, referenced tests exist, changelog touched).
- [ ] AI usage Case 2 (design or implementation phase) and Case 3 (testing phase).
- [ ] Tag `v1.0-first-version`, push, submit.

## M3 — Final version (deadline: week 13)

### Defect detection (`backend/tests/defects/`)
- [ ] Pick one defect (real, or a clearly labelled deliberate one, e.g. mean instead of median in AC1).
- [ ] Keep faulty and fixed versions plus both test-run outputs. Explain defect and expected behaviour.

### Dual implementation (AGENTS.md section 11)
- [ ] One shared prompt + shared tests for `rules/backtest.py` (AC4).
- [ ] Branch `dual/claude-code`: implement with Claude Code.
- [ ] Branch `dual/gemini`: implement with Gemini / Antigravity.
- [ ] `docs/dual-implementation.md`: test results, code differences, working-method comparison. Merge one.

### Change request (AGENTS.md section 10, after instructor issues it)
- [ ] Branch `change-request/<name>` from `v1.0-first-version`.
- [ ] `docs/change-request.md` first: requirement, affected ACs, affected code, solution and reasons.
- [ ] Update `docs/specification.md` + docx, mark changed ACs, stay ≤ 4,000 characters.
- [ ] New migration only; data-preservation test in `tests/regression/`.
- [ ] Regression tests proving old behaviour unchanged.
- [ ] AI usage entry for the change request.

### Wrap-up
- [ ] `CHANGELOG.md` summary of changes v1 → v2.
- [ ] Final traceability with test run results.
- [ ] Tag `v2.0-final`, upload to Moodle.

## Defence preparation

- [ ] Choose one AC and rehearse its verification (~2 min). AC1 or AC4 is a good fit.
- [ ] Be able to explain `surplus.py`, `plan.py`, `backtest.py`, `mandate.py` without AI and predict outputs for given inputs.
- [ ] Practise a small live change + test (e.g. change 70 % to 60 % via `RuleConfig`, update AC1 test).
- [ ] Prepare laptop: `make setup && make seed && make dev` works from a clean clone.

## Out of scope unless needed

AGENTS.md also lists `rules/events.py` (raise/bonus detection), `rules/tax.py` (pension tax credit), `rules/whatif.py` and an APScheduler year-end tax check. No AC requires them. Build them only after M2 is complete, or remove them from AGENTS.md.
