# 0002. Backend rule interpretations and M2 scope
Date: 2026-10-06 · Status: accepted

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
