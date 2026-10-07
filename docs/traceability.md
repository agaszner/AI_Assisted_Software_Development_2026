# Traceability

One row per acceptance criterion (`docs/specification.md`). Test paths are relative to `backend/`.
Status: `planned` (test not written yet) or `passing`. `make docs-check` verifies that every AC has
a row and that every test referenced by a non-planned row exists.

| AC | Requirement (short) | Verification | Test / evidence | Status |
| --- | --- | --- | --- | --- |
| AC1 | Median surplus → 70 % monthly amount (73,500) | automated | tests/rules/test_surplus.py::test_ac1_median_surplus_gives_73500 | passing |
| AC2 | Emergency fund filled before any investment | automated | tests/rules/test_plan.py::test_ac2_emergency_fund_comes_first | planned |
| AC3 | ≤ 12-month money only liquid low-risk; nothing above risk score | automated | tests/rules/test_plan.py::test_ac3_expense_in_10_months_goes_to_liquid_low_risk; tests/rules/test_plan.py::test_ac3_risk_score_2_has_no_product_above_2 | planned |
| AC4 | Time machine replays 12 months, flags skipped months | automated | tests/rules/test_backtest.py::test_ac4_replays_twelve_months; tests/rules/test_backtest.py::test_ac4_month_breaking_minimum_is_flagged_skipped | planned |
| AC5 | Median surplus < 0 → no plan, customer told | automated | tests/rules/test_surplus.py::test_ac5_negative_median_gives_no_amount; tests/api/test_plans_api.py::test_ac5_no_surplus_creates_no_plan | planned |
| AC6 | < 3 months → ask expected savings; 3–5 months → low confidence, each transfer approved | automated | tests/rules/test_confidence.py::test_ac6_two_months_gives_no_estimate; tests/rules/test_confidence.py::test_ac6_four_months_is_low_confidence; tests/services/test_execution.py::test_ac6_low_confidence_transfer_waits_for_approval | planned |
| AC7 | Accept creates orders exactly once; reject creates none | automated | tests/services/test_acceptance.py::test_ac7_accepting_twice_creates_orders_once; tests/services/test_acceptance.py::test_ac7_rejected_plan_creates_no_orders; tests/services/test_execution.py::test_ac7_running_orders_twice_executes_once | planned |
| AC8 | Negative amount / past date → error; other customer's plan → 403 | automated | tests/api/test_plans_api.py::test_ac8_negative_amount_is_rejected; tests/api/test_plans_api.py::test_ac8_past_expense_date_is_rejected; tests/api/test_plans_api.py::test_ac8_other_customer_cannot_view_or_accept_plan | planned |
