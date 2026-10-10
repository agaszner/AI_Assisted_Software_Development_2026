from datetime import UTC, date, datetime
from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.management import CommandError, call_command

from banking.models import Account, Product, Transaction
from core.clock import FixedClock
from plans.execution import approve_execution, get_owned_execution, run_monthly_orders
from plans.models import Execution, LogEntry, Mandate, Plan
from plans.services import (
    PlanConflict,
    accept_plan,
    pause_plan,
    propose_plan,
    submit_questionnaire,
)
from rules.mandate import APPROVAL_CLAUSE, AUTHORISING_CLAUSE, MIN_BALANCE_CLAUSE
from rules.money import Huf
from tests.constants import AC1_SERIES
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db

DANI_SERIES = [50_000, 60_000, 55_000, 65_000]  # 4 months → low confidence, 40,250 HUF


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def accepted_plan(
    clock: FixedClock, username: str, surpluses: list[Huf], *, balance: Huf = 1_000_000
) -> Plan:
    customer = create_customer(username, surpluses, balance=balance)
    submit_questionnaire(
        customer,
        risk_score=3,
        existing_emergency_fund=750_000,  # full: one investment item
        expected_monthly_savings=None,
        planned_expenses=(),
        clock=clock,
    )
    _, plan = propose_plan(customer, clock)
    assert plan is not None
    accept_plan(plan, clock)
    return plan


def signed_in_september() -> None:
    Mandate.objects.update(signed_at=datetime(2026, 9, 10, 12, tzinfo=UTC))


def balance_of(customer: User) -> Huf:
    return Account.objects.get(customer=customer).balance


def test_execution_debits_account_and_logs_mandate_clause(clock: FixedClock) -> None:
    plan = accepted_plan(clock, "anna", AC1_SERIES)
    [execution] = run_monthly_orders(clock)
    assert execution.status == Execution.Status.EXECUTED
    assert (execution.mandate_version, execution.clause) == (1, AUTHORISING_CLAUSE)
    assert balance_of(plan.customer) == 1_000_000 - 73_500
    entry = LogEntry.objects.get(event="execution_executed")
    assert (entry.mandate_version, entry.clause) == (1, AUTHORISING_CLAUSE)
    transfer = Transaction.objects.filter(account__customer=plan.customer).last()
    assert transfer is not None
    assert (transfer.amount, transfer.own_transfer) == (-73_500, True)


def test_ac7_running_orders_twice_executes_once(clock: FixedClock) -> None:
    plan = accepted_plan(clock, "anna", AC1_SERIES)
    run_monthly_orders(clock)
    run_monthly_orders(clock)
    assert Execution.objects.count() == 1
    assert balance_of(plan.customer) == 1_000_000 - 73_500


def test_next_month_executes_again(clock: FixedClock) -> None:
    plan = accepted_plan(clock, "anna", AC1_SERIES)
    run_monthly_orders(clock)
    run_monthly_orders(FixedClock.on(date(2026, 11, 6)))
    assert Execution.objects.count() == 2
    assert balance_of(plan.customer) == 1_000_000 - 2 * 73_500


def test_late_run_keeps_the_scheduled_month(clock: FixedClock) -> None:
    """A late run for September (on 6 October) uses the September key, so October still runs."""
    accepted_plan(clock, "anna", AC1_SERIES)
    signed_in_september()
    [late] = run_monthly_orders(clock, period=date(2026, 9, 1))
    assert (late.period, late.idempotency_key[-7:]) == (date(2026, 9, 1), "2026-09")
    run_monthly_orders(clock)
    run_monthly_orders(clock, period=date(2026, 9, 15))
    periods = sorted(e.period for e in Execution.objects.all())
    assert periods == [date(2026, 9, 1), date(2026, 10, 1)]


def test_no_execution_for_a_month_before_the_mandate(clock: FixedClock) -> None:
    accepted_plan(clock, "anna", AC1_SERIES)  # signed in October
    assert run_monthly_orders(clock, period=date(2026, 9, 1)) == []


def test_future_month_is_refused(clock: FixedClock) -> None:
    accepted_plan(clock, "anna", AC1_SERIES)
    with pytest.raises(PlanConflict):
        run_monthly_orders(clock, period=date(2026, 11, 1))
    with pytest.raises(CommandError, match="future month"):
        call_command("run_orders", "--period", "2026-11", stdout=StringIO())
    assert Execution.objects.count() == 0


def test_run_orders_command_takes_a_period(clock: FixedClock) -> None:
    accepted_plan(clock, "anna", AC1_SERIES)
    signed_in_september()
    call_command("run_orders", "--period", "2026-09", stdout=StringIO())
    assert Execution.objects.get().period == date(2026, 9, 1)


def test_transfer_below_minimum_balance_is_denied(clock: FixedClock) -> None:
    plan = accepted_plan(clock, "anna", AC1_SERIES, balance=120_000)
    [execution] = run_monthly_orders(clock)
    assert (execution.status, execution.clause) == (Execution.Status.DENIED, MIN_BALANCE_CLAUSE)
    assert balance_of(plan.customer) == 120_000


def test_ac6_low_confidence_transfer_waits_for_approval(clock: FixedClock) -> None:
    plan = accepted_plan(clock, "dani", DANI_SERIES)
    [execution] = run_monthly_orders(clock)
    assert execution.status == Execution.Status.AWAITING_APPROVAL
    assert execution.clause == APPROVAL_CLAUSE
    assert balance_of(plan.customer) == 1_000_000

    approved = approve_execution(execution, clock)
    assert approved.pk == execution.pk
    assert approved.status == Execution.Status.EXECUTED
    assert balance_of(plan.customer) == 1_000_000 - 40_250
    with pytest.raises(PlanConflict):
        approve_execution(approved, clock)
    run_monthly_orders(clock)
    assert Execution.objects.count() == 1


def test_paused_plan_executes_nothing(clock: FixedClock) -> None:
    plan = accepted_plan(clock, "anna", AC1_SERIES)
    pause_plan(plan, clock)
    assert run_monthly_orders(clock) == []
    assert Execution.objects.count() == 0


def test_other_customer_cannot_approve(clock: FixedClock) -> None:
    accepted_plan(clock, "dani", DANI_SERIES)
    [execution] = run_monthly_orders(clock)
    other = create_customer("bob", AC1_SERIES)
    with pytest.raises(PermissionDenied):
        get_owned_execution(other, execution.pk)


def test_run_orders_command(clock: FixedClock) -> None:
    accepted_plan(clock, "anna", AC1_SERIES)
    out = StringIO()
    call_command("run_orders", stdout=out)
    assert "1 orders processed: executed=1" in out.getvalue()
