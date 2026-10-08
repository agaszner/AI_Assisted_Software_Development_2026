from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import Http404

from banking.models import Product
from core.clock import FixedClock
from plans.models import LogEntry, Mandate, Plan, QuestionnaireAnswer, RecurringOrder
from plans.services import (
    InvalidInput,
    PlanConflict,
    accept_plan,
    active_plan,
    edit_amount,
    get_owned_plan,
    pause_plan,
    propose_plan,
    reject_plan,
    submit_questionnaire,
    time_machine,
)
from rules.money import Huf
from rules.plan import Outcome
from rules.types import PlannedExpense
from tests.constants import AC1_SERIES, TODAY
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def answer(
    customer: User,
    clock: FixedClock,
    *,
    fund: Huf = 0,
    expected: Huf | None = None,
    expenses: tuple[PlannedExpense, ...] = (),
) -> QuestionnaireAnswer:
    return submit_questionnaire(
        customer,
        risk_score=3,
        existing_emergency_fund=fund,
        expected_monthly_savings=expected,
        planned_expenses=expenses,
        clock=clock,
    )


def proposed_plan(clock: FixedClock, username: str = "anna", fund: Huf = 0) -> Plan:
    customer = create_customer(username, AC1_SERIES)
    answer(customer, clock, fund=fund)
    _, plan = propose_plan(customer, clock)
    assert plan is not None
    return plan


def test_proposal_stores_plan_with_emergency_fund_first(clock: FixedClock) -> None:
    plan = proposed_plan(clock)
    assert plan.status == Plan.Status.PROPOSED
    assert plan.monthly_amount == 73_500
    assert [item.kind for item in plan.items.all()] == ["emergency_fund"]
    assert LogEntry.objects.filter(event="plan_proposed").count() == 1


def test_ac5_no_surplus_stores_no_plan(clock: FixedClock) -> None:
    customer = create_customer("bence", [-40_000] * 6)
    answer(customer, clock)
    proposal, plan = propose_plan(customer, clock)
    assert proposal.outcome is Outcome.NO_SURPLUS
    assert plan is None
    assert Plan.objects.count() == 0


def test_ac6_short_history_stores_no_plan_without_expected_savings(clock: FixedClock) -> None:
    customer = create_customer("csilla", [60_000, 70_000])
    answer(customer, clock)
    proposal, plan = propose_plan(customer, clock)
    assert proposal.outcome is Outcome.NEEDS_EXPECTED_SAVINGS
    assert plan is None


def test_proposal_without_questionnaire_is_a_conflict(clock: FixedClock) -> None:
    with pytest.raises(PlanConflict):
        propose_plan(create_customer("anna", AC1_SERIES), clock)


def test_ac7_accepting_twice_creates_orders_once(clock: FixedClock) -> None:
    plan = proposed_plan(clock, fund=700_000)  # two items: emergency fund + investment
    first = accept_plan(plan, clock)
    second = accept_plan(plan, clock)
    assert len(first) == 2
    assert {o.pk for o in second} == {o.pk for o in first}
    assert RecurringOrder.objects.count() == 2
    assert Mandate.objects.count() == 1
    assert LogEntry.objects.filter(event="plan_accepted").count() == 1


def test_ac7_rejected_plan_creates_no_orders(clock: FixedClock) -> None:
    plan = proposed_plan(clock)
    reject_plan(plan, clock)
    with pytest.raises(PlanConflict):
        accept_plan(plan, clock)
    assert RecurringOrder.objects.count() == 0
    assert Mandate.objects.count() == 0


def test_acceptance_signs_a_new_mandate_version(clock: FixedClock) -> None:
    plan = proposed_plan(clock)
    accept_plan(plan, clock)
    pause_plan(plan, clock)
    _, second = propose_plan(plan.customer, clock)
    assert second is not None
    accept_plan(second, clock)
    assert sorted(Mandate.objects.values_list("version", flat=True)) == [1, 2]


def test_second_active_plan_is_a_conflict(clock: FixedClock) -> None:
    plan = proposed_plan(clock)
    accept_plan(plan, clock)
    _, second = propose_plan(plan.customer, clock)
    assert second is not None
    with pytest.raises(PlanConflict):
        accept_plan(second, clock)


def test_edit_amount_reallocates_and_stays_proposed(clock: FixedClock) -> None:
    plan = edit_amount(proposed_plan(clock, fund=700_000), 50_000, clock)
    assert plan.status == Plan.Status.PROPOSED
    assert sum(item.monthly_amount for item in plan.items.all()) == 50_000
    assert [item.kind for item in plan.items.all()] == ["emergency_fund"]
    assert RecurringOrder.objects.count() == 0


@pytest.mark.parametrize("amount", [0, -5, 73_501])
def test_edit_amount_outside_range_is_invalid(clock: FixedClock, amount: Huf) -> None:
    with pytest.raises(InvalidInput):
        edit_amount(proposed_plan(clock), amount, clock)


def test_ac8_past_expense_date_is_rejected_by_service(clock: FixedClock) -> None:
    customer = create_customer("anna", AC1_SERIES)
    yesterday = PlannedExpense("Car", 500_000, TODAY - timedelta(days=1))
    with pytest.raises(InvalidInput):
        answer(customer, clock, expenses=(yesterday,))
    answer(customer, clock, expenses=(PlannedExpense("Car", 500_000, TODAY),))  # today is fine


def test_ac8_other_customers_plan_is_forbidden(clock: FixedClock) -> None:
    plan = proposed_plan(clock)
    other = create_customer("bob", AC1_SERIES)
    with pytest.raises(PermissionDenied):
        get_owned_plan(other, plan.pk)
    with pytest.raises(Http404):
        get_owned_plan(other, plan.pk + 999)
    assert get_owned_plan(plan.customer, plan.pk) == plan


def test_pause_pauses_mandate_and_orders(clock: FixedClock) -> None:
    plan = proposed_plan(clock)
    accept_plan(plan, clock)
    pause_plan(plan, clock)
    plan.refresh_from_db()
    assert plan.status == Plan.Status.PAUSED
    assert Mandate.objects.get(plan=plan).status == Mandate.Status.PAUSED
    assert set(RecurringOrder.objects.values_list("status", flat=True)) == {"paused"}
    assert active_plan(plan.customer) == plan


def test_pausing_a_proposed_plan_is_a_conflict(clock: FixedClock) -> None:
    with pytest.raises(PlanConflict):
        pause_plan(proposed_plan(clock), clock)


def test_no_eligible_product_is_a_conflict(clock: FixedClock) -> None:
    Product.objects.update(active=False)
    customer = create_customer("anna", AC1_SERIES)
    answer(customer, clock)
    with pytest.raises(PlanConflict):
        propose_plan(customer, clock)


def test_time_machine_replays_the_plan(clock: FixedClock) -> None:
    result = time_machine(proposed_plan(clock), clock)
    assert len(result.months) == 6
    assert result.total_saved == 6 * 73_500


def test_ac7_stale_copy_cannot_reject_an_accepted_plan(clock: FixedClock) -> None:
    plan = proposed_plan(clock)
    stale = Plan.objects.get(pk=plan.pk)
    accept_plan(plan, clock)
    with pytest.raises(PlanConflict):
        reject_plan(stale, clock)
    assert Plan.objects.get(pk=plan.pk).status == Plan.Status.ACCEPTED
