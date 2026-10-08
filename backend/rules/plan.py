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
        product = pick_product(
            products, max_risk=risk_score, liquid_only=False, horizon_months=None
        )
        items.append(
            PlanItemDraft(
                ItemKind.INVESTMENT, "Long-term investment", product, remaining, None, None
            )
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
