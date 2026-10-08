from collections.abc import Sequence
from datetime import date

import pytest

from banking.synthetic import monthly_series
from rules.confidence import Confidence
from rules.money import Huf
from rules.plan import (
    ItemKind,
    NoEligibleProduct,
    Outcome,
    PlanInputs,
    PlanItemDraft,
    allocate,
    propose,
)
from rules.types import PlannedExpense, ProductInfo
from tests.constants import AC1_SERIES, LAST_MONTH, TODAY

MONEY_MARKET = ProductInfo(1, "Money market fund", 1, 0, True)
SHORT_BOND = ProductInfo(2, "Short government bond fund", 2, 0, True)
BALANCED = ProductInfo(3, "Balanced fund", 3, 36, False)
EQUITY = ProductInfo(4, "Global equity fund", 5, 60, False)
CATALOGUE = (MONEY_MARKET, SHORT_BOND, BALANCED, EQUITY)
FULL_FUND = 750_000  # 3 × 250,000 median expenses


def plan_for(
    amount: Huf,
    *,
    risk: int = 5,
    fund: Huf = FULL_FUND,
    expenses: Sequence[PlannedExpense] = (),
    median_expenses: Huf = 250_000,
    products: Sequence[ProductInfo] = CATALOGUE,
) -> tuple[PlanItemDraft, ...]:
    return allocate(
        amount,
        median_expenses=median_expenses,
        risk_score=risk,
        existing_emergency_fund=fund,
        planned_expenses=expenses,
        today=TODAY,
        products=products,
    )


def summary(items: Sequence[PlanItemDraft]) -> list[tuple[ItemKind, Huf]]:
    return [(item.kind, item.monthly_amount) for item in items]


def test_ac2_emergency_fund_comes_first() -> None:
    items = plan_for(73_500, fund=0)
    assert summary(items) == [(ItemKind.EMERGENCY_FUND, 73_500)]
    assert items[0].target_amount == 750_000
    assert items[0].product.liquid


def test_ac2_investment_gets_only_what_is_left() -> None:
    items = plan_for(73_500, fund=700_000)
    assert summary(items) == [(ItemKind.EMERGENCY_FUND, 50_000), (ItemKind.INVESTMENT, 23_500)]
    assert items[1].product == EQUITY


def test_full_emergency_fund_skips_emergency_item() -> None:
    assert summary(plan_for(73_500)) == [(ItemKind.INVESTMENT, 73_500)]


def test_ac3_expense_in_10_months_goes_to_liquid_low_risk() -> None:
    car = PlannedExpense("Car", 500_000, date(2027, 8, 15))  # October 2026 → August 2027
    items = plan_for(73_500, expenses=[car])
    assert summary(items) == [(ItemKind.PLANNED_EXPENSE, 50_000), (ItemKind.INVESTMENT, 23_500)]
    assert items[0].horizon_months == 10
    assert items[0].product.liquid
    assert items[0].product.risk_level <= 2


def test_ac3_risk_score_2_has_no_product_above_2() -> None:
    renovation = PlannedExpense("Renovation", 240_000, date(2028, 10, 1))  # 24 months
    items = plan_for(300_000, risk=2, fund=0, median_expenses=50_000, expenses=[renovation])
    assert summary(items) == [
        (ItemKind.EMERGENCY_FUND, 150_000),
        (ItemKind.PLANNED_EXPENSE, 10_000),
        (ItemKind.INVESTMENT, 140_000),
    ]
    assert max(item.product.risk_level for item in items) <= 2


def test_twelve_months_is_short_term_and_thirteen_is_not() -> None:
    one_year_bond = ProductInfo(5, "One-year corporate bond", 3, 12, False)
    catalogue = (*CATALOGUE, one_year_bond)
    in_12 = plan_for(
        73_500, expenses=[PlannedExpense("Trip", 120_000, date(2027, 10, 1))], products=catalogue
    )
    in_13 = plan_for(
        73_500, expenses=[PlannedExpense("Trip", 130_000, date(2027, 11, 1))], products=catalogue
    )
    assert in_12[0].product == SHORT_BOND
    assert in_13[0].product == one_year_bond


def test_expense_due_this_month_needs_full_amount_now() -> None:
    insurance = PlannedExpense("Insurance", 60_000, date(2026, 10, 20))
    items = plan_for(73_500, expenses=[insurance])
    assert summary(items) == [(ItemKind.PLANNED_EXPENSE, 60_000), (ItemKind.INVESTMENT, 13_500)]
    assert items[0].horizon_months == 1


def test_planned_expenses_are_ordered_by_due_date() -> None:
    later = PlannedExpense("Later", 100_000, date(2027, 9, 1))
    sooner = PlannedExpense("Sooner", 100_000, date(2027, 1, 1))
    items = plan_for(73_500, expenses=[later, sooner])
    assert [item.label for item in items[:2]] == ["Sooner", "Later"]


def test_no_eligible_product_raises() -> None:
    with pytest.raises(NoEligibleProduct):
        plan_for(73_500, fund=0, products=(EQUITY,))


def inputs(surpluses: list[Huf], *, expected: Huf | None = None) -> PlanInputs:
    return PlanInputs(
        today=TODAY,
        risk_score=5,
        existing_emergency_fund=FULL_FUND,
        expected_monthly_savings=expected,
        planned_expenses=(),
        transactions=monthly_series(LAST_MONTH, surpluses),
    )


def test_ac1_proposal_uses_73500() -> None:
    proposal = propose(inputs(AC1_SERIES), CATALOGUE)
    assert proposal.outcome is Outcome.PLAN
    assert proposal.monthly_amount == 73_500
    assert proposal.confidence is Confidence.NORMAL
    assert summary(proposal.items) == [(ItemKind.INVESTMENT, 73_500)]


def test_ac5_no_surplus_gives_no_plan() -> None:
    proposal = propose(inputs([-50_000] * 6), CATALOGUE)
    assert proposal.outcome is Outcome.NO_SURPLUS
    assert proposal.items == ()


def test_ac6_too_little_data_asks_for_expected_savings() -> None:
    proposal = propose(inputs([60_000, 70_000]), CATALOGUE)
    assert proposal.outcome is Outcome.NEEDS_EXPECTED_SAVINGS
    assert proposal.items == ()


def test_ac6_expected_savings_are_used_when_data_is_short() -> None:
    proposal = propose(inputs([60_000, 70_000], expected=40_000), CATALOGUE)
    assert proposal.outcome is Outcome.PLAN
    assert proposal.monthly_amount == 40_000
    assert proposal.confidence is Confidence.NONE


def test_ac6_four_months_gives_low_confidence_plan() -> None:
    proposal = propose(inputs([50_000, 60_000, 55_000, 65_000]), CATALOGUE)
    assert proposal.outcome is Outcome.PLAN
    assert proposal.confidence is Confidence.LOW
