# Manual checks

Reproducible checks for behaviour that is easiest to see in the running app.
The customer API arrives with backend plan Task 13 and the UI with the frontend plan, so until then
the checks use Django admin and `manage.py shell`. They will be rewritten against the API and UI.

Setup for every check (from a clean database, so the numbers match). Set
`SAVERAI_FIXED_DATE=2026-10-06` in `.env` first: `make seed` dates its personas from that day, and
the Makefile's `.env` values override shell variables. Then:

    rm -f backend/db.sqlite3 && make seed
    cd backend && export SAVERAI_FIXED_DATE=2026-10-06   # same date for manage.py

Passwords: `SEED_PASSWORD` from `.env`. Last run: 2026-10-10, all expected results seen.

## RuleConfig change (defence rehearsal, AC1)
1. `make dev`, open http://localhost:8000/admin/, log in as `admin`.
2. Rule configuration → set "Monthly share percent" to 60 → Save.
3. Run:

       uv run python manage.py shell -c 'from django.contrib.auth.models import User; from core.clock import get_clock; from plans.services import analyse; print(analyse(User.objects.get(username="anna"), get_clock())[0].monthly_amount)'

Expected: `63000` (60 % of the 105,000 HUF median). Set it back to 70 → the same command prints `73500`.

## AC4 — time machine skipped months
Run:

    uv run python manage.py shell -c '
    from django.contrib.auth.models import User
    from banking.models import Account
    from core.clock import get_clock
    from plans.services import submit_questionnaire, propose_plan, time_machine
    anna = User.objects.get(username="anna"); clock = get_clock()
    submit_questionnaire(anna, risk_score=3, existing_emergency_fund=750000,
                         expected_monthly_savings=None, planned_expenses=(), clock=clock)
    _, plan = propose_plan(anna, clock)
    Account.objects.filter(customer=anna).update(balance=300000)
    for m in time_machine(plan, clock).months: print(m.month, m.transfer, m.skipped)'

Expected: six months (anna has 6 months of data). April–August 2026 print `0 True` (the transfer
would have left less than 100,000 HUF), September 2026 prints `73500 False`.

## AC6 and AC7 — order execution
1. Accept a plan for `dani` (4 months of data, low confidence):

       uv run python manage.py shell -c '
       from django.contrib.auth.models import User
       from core.clock import get_clock
       from plans.services import submit_questionnaire, propose_plan, accept_plan
       dani = User.objects.get(username="dani"); clock = get_clock()
       submit_questionnaire(dani, risk_score=3, existing_emergency_fund=750000,
                            expected_monthly_savings=None, planned_expenses=(), clock=clock)
       _, plan = propose_plan(dani, clock); accept_plan(plan, clock)'

2. Run `uv run python manage.py run_orders` twice.
   Expected: both runs print `1 orders processed: awaiting_approval=1` (clause 3, nothing is debited,
   and the second run creates no new execution).
3. Approve the transfer:

       uv run python manage.py shell -c 'from core.clock import get_clock; from plans.models import Execution; from plans.execution import approve_execution; e = approve_execution(Execution.objects.get(), get_clock()); print(e.idempotency_key, e.status, e.mandate_version, e.clause)'

   Expected: `order-1-2026-10 executed 1 1`. dani's account balance in Django admin is 40,250 HUF lower.
4. In Django admin → Log entries: `execution_awaiting_approval` (mandate v1, clause 3) and
   `execution_executed` (mandate v1, clause 1).
5. `uv run python manage.py run_orders --period 2026-13`.
   Expected: `argument --period: invalid year_month value: '2026-13'`, nothing executed.
   `--period 2026-11` prints `CommandError: Orders cannot be executed for a future month.`

## Product catalogue (Admin role)
1. In Django admin, add a product with risk level 6.
Expected: the form rejects it: `Constraint “product_risk_level_1_to_5” is violated.`
