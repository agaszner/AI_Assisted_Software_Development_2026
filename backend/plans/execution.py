"""Monthly execution of recurring orders.

Every transfer passes rules.mandate.check_action() (golden rule 6). The Execution row and the
log entry store the mandate version and clause. A unique idempotency key per order and month
makes repeated runs harmless (AC7).
"""

from datetime import date

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Sum
from django.http import Http404

from banking.models import Account, Transaction
from core.clock import Clock
from plans.models import Execution, Mandate, RecurringOrder
from plans.services import PlanConflict, log_event
from rules.mandate import APPROVAL_CLAUSE, TransferAction, check_action
from rules.months import add_months, month_of


def idempotency_key(order: RecurringOrder, period: date) -> str:
    return f"order-{order.pk}-{period:%Y-%m}"


def run_monthly_orders(clock: Clock, period: date | None = None) -> list[Execution]:
    """Execute every active order once for `period` (default: the current calendar month).
    The key uses the month being executed, not the run date, so a late run for September on
    2 October neither skips September nor takes October's slot (AI usage Case 2)."""
    current = month_of(clock.today())
    period = month_of(period or current)
    if period > current:
        raise PlanConflict("Orders cannot be executed for a future month.")
    orders = RecurringOrder.objects.filter(
        status=RecurringOrder.Status.ACTIVE,
        mandate__signed_at__date__lt=add_months(period, 1),  # no month before the mandate
    ).order_by("id")
    return [execute_order(order, period, clock) for order in orders]


def execute_order(
    order: RecurringOrder, period: date, clock: Clock, *, approved: bool = False
) -> Execution:
    """Run one order for one month. Returns the existing execution if there is one, unless the
    customer is approving a transfer that was waiting for approval (AC6)."""
    key = idempotency_key(order, period)
    with transaction.atomic():
        existing = Execution.objects.select_for_update().filter(idempotency_key=key).first()
        approving = (
            approved
            and existing is not None
            and existing.status == Execution.Status.AWAITING_APPROVAL
        )
        if existing is not None and not approving:
            return existing
        mandate = Mandate.objects.select_related("customer", "plan").get(pk=order.mandate_id)
        account = Account.objects.select_for_update().get(customer_id=mandate.customer_id)
        already = (
            Execution.objects.filter(
                order__mandate=mandate, period=period, status=Execution.Status.EXECUTED
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        decision = check_action(
            mandate.terms(),
            TransferAction(
                product_id=order.product_id,
                amount=order.monthly_amount,
                balance_before=account.balance,
                transferred_this_month=already,
                approved_by_customer=approved,
            ),
        )
        if decision.allowed:
            status = Execution.Status.EXECUTED
            account.balance -= order.monthly_amount
            account.save(update_fields=["balance"])
            Transaction.objects.create(
                account=account,
                booked_on=clock.today(),
                amount=-order.monthly_amount,
                description=f"SaverAI order {order.pk}",
                own_transfer=True,  # savings transfer: excluded from future surplus analysis
            )
        elif decision.clause == APPROVAL_CLAUSE:
            status = Execution.Status.AWAITING_APPROVAL
        else:
            status = Execution.Status.DENIED
        execution, _ = Execution.objects.update_or_create(
            idempotency_key=key,
            defaults={
                "order": order,
                "period": period,
                "status": status,
                "amount": order.monthly_amount,
                "mandate_version": decision.mandate_version,
                "clause": decision.clause,
                "reason": decision.reason,
                "created_at": clock.now(),
            },
        )
        log_event(
            mandate.customer,
            f"execution_{status.value}",
            f"Order {order.pk}, {period:%Y-%m}: {decision.reason}",
            clock,
            plan=mandate.plan,
            mandate_version=decision.mandate_version,
            clause=decision.clause,
        )
    return execution


def get_owned_execution(customer: User, execution_id: int) -> Execution:
    """404 if missing, 403 if it belongs to another customer (AC8)."""
    execution = Execution.objects.select_related("order__mandate").filter(pk=execution_id).first()
    if execution is None:
        raise Http404("Transfer not found.")
    if execution.order.mandate.customer_id != customer.pk:
        raise PermissionDenied("This transfer belongs to another customer.")
    return execution


def approve_execution(execution: Execution, clock: Clock) -> Execution:
    """The customer approves one transfer of a plan without normal confidence (AC6)."""
    if execution.status != Execution.Status.AWAITING_APPROVAL:
        raise PlanConflict("Only a transfer that is waiting for approval can be approved.")
    return execute_order(execution.order, execution.period, clock, approved=True)
