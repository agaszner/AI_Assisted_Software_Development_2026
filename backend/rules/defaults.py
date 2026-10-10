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
