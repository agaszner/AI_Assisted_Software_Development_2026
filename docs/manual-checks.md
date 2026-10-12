# Manual checks

Reproducible checks for behaviour that is easiest to see in the running app.
The checks use Django admin and `manage.py shell` so that each step is one copy-paste; the same
data is available through the API (http://localhost:8000/api/docs). UI-only checks (layout,
focus, screens) are in the "UI checks" section below.

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

# UI checks

Automated by `make e2e` (Playwright, 1440 px and 375 px): main flow, AC5 path, 44 px targets and
no horizontal scroll on Home and Plan review. The checks below cover what the e2e does not assert.

Setup: `SAVERAI_FIXED_DATE=2026-10-08` in `.env`, then
`rm -f backend/db.sqlite3 && make seed && make dev`. Open http://localhost:5173 (1440 px wide).
Password for every persona: `SEED_PASSWORD` from `.env`. Status: steps drafted 2026-10-12 from the
screens and their tests; author to run and record the date here.

## AC4 — time machine skipped months (UI)
1. Django admin (http://localhost:8000/admin/) → anna's account → balance 300000 → Save.
2. Log in as `anna` → Start a savings plan → fund 0, risk 3 → Continue → See my plan → See month by month.
Expected: skipped months are grey bars with a dashed amber outline and a warning marker; the
"Skipped months" card lists the backend note ("…would have left less than 100,000 HUF…");
"Months skipped" shows their count; "See month by month" opens a table where those months show 0.

## Mandate signing (UI, AC7)
1. Log in as `anna` → Start a savings plan → fund 0, risk 3 → Continue → See my plan → See month
   by month → Continue to mandate.
Expected: "Mandate · version 1" with terms and numbered clauses; "Sign mandate" is disabled until the
consent checkbox is ticked.
2. Tick the consent → Sign mandate → enter a wrong password → Confirm and sign.
Expected: "Incorrect password." in the dialog, the dialog stays open, nothing is signed.
3. Enter the right password → press Enter twice quickly.
Expected: one signing; "Your savings plan" shows "Active" and "Scheduled" rows in the execution log.
Reopen the mandate URL: "Version 1, signed …", no "Sign mandate" button.

## Active plan — pause (UI)
1. Continue from the previous check (anna with an active plan) → Savings plan → Pause plan.
Expected: dialog "Pause your savings plan?"; Esc or Cancel keeps the plan "Active".
2. Pause plan → Pause plan in the dialog.
Expected: badge "Paused", the "Pause plan" button is gone, the execution log adds
"Plan paused: mandate version 1 stopped (§4)". `cd backend && uv run python manage.py run_orders`
executes nothing for anna.

## AC6 — approving a transfer (UI)
1. Log in as `dani` → Start a savings plan → fund 0, risk 3 → Continue → See my plan.
Expected: "Low confidence" badge and "Every transfer needs your approval".
2. Continue to mandate → tick the consent → Sign mandate → password → Confirm and sign.
3. Terminal: `cd backend && uv run python manage.py run_orders`.
4. Reload "Savings plan".
Expected: the log row shows "Needs approval"; its audit details show "§3". Press "Approve".
Expected: the row changes to "Done".

## Change amount → mandate version 2 (UI)
1. As `anna` with an active plan: Savings plan → Change amount → 50000 → Propose new amount.
Expected: plan review of the new amount; the old plan still shows "Active" until signing.
2. Continue to mandate. Expected: "Mandate · version 2". Sign with the password.
Expected: Savings plan shows mandate version 2; the log keeps version 1 and adds
"Plan paused: mandate version 1 stopped (§4)".

## Keyboard and focus
1. On every screen, press Tab through all controls.
Expected: every control shows the focus ring; order follows the screen.
2. Questionnaire: arrow keys change the risk score; Enter submits. Password dialog: focus stays
inside, Esc closes, Enter confirms.

## Responsive (900 px and 375 px)
1. Resize to 900 px. Expected: the sidebar becomes a top bar with "Open menu"; the menu opens a
drawer; Esc closes it. Plan review and Mandate stack; the summary panel is a bottom bar.
2. Resize to 375 px. Expected: one column, no horizontal scrolling on any screen (Home, questionnaire,
analysis, plan review, time machine, mandate, Savings plan, Activity); the execution log shows
stacked rows (date and status on top, event, amount).
