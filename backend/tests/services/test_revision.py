import pytest

from banking.models import Product
from core.clock import FixedClock
from plans.models import Mandate, Plan, RecurringOrder
from plans.services import (
    InvalidInput,
    PlanConflict,
    accept_plan,
    active_plan,
    propose_plan,
    reject_plan,
    revise_plan,
    submit_questionnaire,
)
from tests.constants import AC1_SERIES
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def accepted_plan(clock: FixedClock) -> Plan:
    customer = create_customer("anna", AC1_SERIES)
    submit_questionnaire(
        customer,
        risk_score=3,
        existing_emergency_fund=0,
        expected_monthly_savings=None,
        planned_expenses=(),
        clock=clock,
    )
    _, plan = propose_plan(customer, clock)
    assert plan is not None
    accept_plan(plan, clock)
    plan.refresh_from_db()
    return plan


def test_revision_keeps_the_active_plan_running_until_signed(clock: FixedClock) -> None:
    plan = accepted_plan(clock)
    revision = revise_plan(plan, 50_000, clock)
    plan.refresh_from_db()
    assert (revision.status, revision.revises_id, revision.monthly_amount) == (
        "proposed",
        plan.pk,
        50_000,
    )
    assert sum(item.monthly_amount for item in revision.items.all()) == 50_000
    assert plan.status == Plan.Status.ACCEPTED
    assert not RecurringOrder.objects.filter(plan_item__plan=plan, status="paused").exists()


def test_signing_a_revision_pauses_the_old_plan_and_signs_version_2(clock: FixedClock) -> None:
    plan = accepted_plan(clock)
    revision = revise_plan(plan, 50_000, clock)
    accept_plan(revision, clock)
    plan.refresh_from_db()
    assert plan.status == Plan.Status.PAUSED
    assert Mandate.objects.get(plan=plan).status == Mandate.Status.PAUSED
    assert set(
        RecurringOrder.objects.filter(plan_item__plan=plan).values_list("status", flat=True)
    ) == {"paused"}
    assert Mandate.objects.get(plan=revision).version == 2
    assert active_plan(plan.customer) == revision


def test_ac7_signing_a_revision_twice_creates_orders_once(clock: FixedClock) -> None:
    revision = revise_plan(accepted_plan(clock), 50_000, clock)
    accept_plan(revision, clock)
    accept_plan(revision, clock)
    assert RecurringOrder.objects.filter(plan_item__plan=revision).count() == revision.items.count()


def test_rejecting_a_revision_leaves_the_plan_running(clock: FixedClock) -> None:
    plan = accepted_plan(clock)
    reject_plan(revise_plan(plan, 50_000, clock), clock)
    plan.refresh_from_db()
    assert plan.status == Plan.Status.ACCEPTED
    assert revise_plan(plan, 40_000, clock).status == Plan.Status.PROPOSED  # a new try is allowed


def test_revising_twice_is_a_conflict(clock: FixedClock) -> None:
    plan = accepted_plan(clock)
    revise_plan(plan, 50_000, clock)
    with pytest.raises(PlanConflict, match="already waiting"):
        revise_plan(plan, 40_000, clock)


def test_revision_above_proposed_amount_is_rejected(clock: FixedClock) -> None:
    plan = accepted_plan(clock)
    with pytest.raises(InvalidInput, match="between 1 and 73500"):
        revise_plan(plan, 73_501, clock)
    assert not Plan.objects.filter(revises=plan).exists()


def test_only_an_active_plan_can_be_revised(clock: FixedClock) -> None:
    plan = accepted_plan(clock)
    revision = revise_plan(plan, 50_000, clock)
    with pytest.raises(PlanConflict, match="Only an active plan"):
        revise_plan(revision, 40_000, clock)
