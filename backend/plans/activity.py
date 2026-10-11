"""Rows of the customer's execution log (Figma 08): the next scheduled transfer of each active
order, every execution with its audit fields, and plan events. Titles come from templates."""

from dataclasses import dataclass
from datetime import date, datetime

from django.contrib.auth.models import User

from core.clock import Clock
from plans import explanations
from plans.execution import idempotency_key
from plans.models import Execution, LogEntry, Plan, RecurringOrder
from plans.services import active_plan
from rules.money import Huf
from rules.months import next_transfer_on

EVENT_STATUS = {
    "plan_proposed": "proposed",
    "plan_revised": "proposed",
    "plan_edited": "done",
    "plan_accepted": "done",
    "plan_rejected": "rejected",
    "plan_paused": "paused",
}


@dataclass(frozen=True)
class ActivityRow:
    key: str
    on: date
    title: str
    amount: Huf | None
    status: str
    mandate_version: int | None
    clause: str | None
    idempotency_key: str | None
    logged_at: datetime | None
    execution_id: int | None


def _scheduled(plan: Plan | None, period: date) -> list[ActivityRow]:
    if plan is None or plan.status != Plan.Status.ACCEPTED:
        return []
    orders = (
        RecurringOrder.objects.filter(plan_item__plan=plan, status=RecurringOrder.Status.ACTIVE)
        .select_related("plan_item", "mandate")
        .order_by("id")
    )
    return [
        ActivityRow(
            key=f"scheduled-{order.pk}-{period:%Y-%m}",
            on=period,
            title=explanations.transfer_title(
                order.plan_item.kind, order.plan_item.label, order.monthly_amount
            ),
            amount=order.monthly_amount,
            status="scheduled",
            mandate_version=order.mandate.version,
            clause=explanations.scheduled_check(order.mandate.per_transfer_approval),
            idempotency_key=idempotency_key(order, period),
            logged_at=None,
            execution_id=None,
        )
        for order in orders
        if not Execution.objects.filter(idempotency_key=idempotency_key(order, period)).exists()
    ]


def _executions(customer: User) -> list[ActivityRow]:
    rows = Execution.objects.filter(order__mandate__customer=customer).select_related(
        "order__plan_item"
    )
    return [
        ActivityRow(
            key=f"execution-{e.pk}",
            on=e.period,
            title=explanations.transfer_title(
                e.order.plan_item.kind, e.order.plan_item.label, e.amount
            ),
            amount=e.amount,
            status=e.status,
            mandate_version=e.mandate_version,
            clause=explanations.decision_text(e.clause, e.reason),
            idempotency_key=e.idempotency_key,
            logged_at=e.created_at,
            execution_id=e.pk,
        )
        for e in rows
    ]


def _events(customer: User) -> list[ActivityRow]:
    rows = []
    for entry in LogEntry.objects.filter(customer=customer, event__in=EVENT_STATUS).select_related(
        "plan"
    ):
        orders = entry.plan.items.count() if entry.plan is not None else 0
        title = explanations.event_title(
            entry.event, amount=entry.amount, version=entry.mandate_version, orders=orders
        )
        if title is None:
            continue
        rows.append(
            ActivityRow(
                key=f"event-{entry.pk}",
                on=entry.created_at.date(),
                title=title,
                amount=entry.amount,
                status=EVENT_STATUS[entry.event],
                mandate_version=entry.mandate_version,
                clause=None,
                idempotency_key=None,
                logged_at=entry.created_at,
                execution_id=None,
            )
        )
    return rows


def _newest_first(row: ActivityRow) -> tuple[date, datetime, int]:
    """Sort key: date, log time, then database id (FixedClock gives equal log times in tests)."""
    assert row.logged_at is not None  # executions and events are always logged
    return (row.on, row.logged_at, int(row.key.rsplit("-", 1)[1]))


def activity(customer: User, clock: Clock) -> list[ActivityRow]:
    """Newest first: scheduled transfers, then executions and events."""
    scheduled = _scheduled(active_plan(customer), next_transfer_on(clock.today()))
    logged = sorted(_executions(customer) + _events(customer), key=_newest_first, reverse=True)
    return scheduled + logged
