"""Plan services: questionnaire, proposal, acceptance, rejection, editing, pausing.

The rule engine decides every number; these functions only load inputs, call `rules`,
store results and keep the audit log. Time always comes from the injected Clock.
"""

from collections.abc import Sequence

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Max, Sum
from django.http import Http404

from banking.models import Account, Product, Transaction
from core.clock import Clock
from plans.models import (
    Execution,
    ExpenseAnswer,
    LogEntry,
    Mandate,
    Plan,
    PlanItem,
    QuestionnaireAnswer,
    RecurringOrder,
    RuleConfig,
)
from rules.backtest import BacktestResult, backtest
from rules.confidence import Confidence, assess_confidence
from rules.mandate import PAUSE_CLAUSE
from rules.money import Huf
from rules.plan import (
    ItemKind,
    NoEligibleProduct,
    Outcome,
    PlanInputs,
    PlanItemDraft,
    Proposal,
    allocate,
    propose,
)
from rules.surplus import SurplusAnalysis, analyse_surplus
from rules.types import PlannedExpense, ProductInfo, Txn


class InvalidInput(Exception):
    """Well-formed input that breaks a business rule (HTTP 422). `field` names the input, e.g.
    "planned_expenses.1.due_on", so the UI can show the message next to it."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class PlanConflict(Exception):
    """The action is not allowed in the current state (HTTP 409)."""


def log_event(
    customer: User,
    event: str,
    message: str,
    clock: Clock,
    *,
    plan: Plan | None = None,
    mandate_version: int | None = None,
    clause: int | None = None,
    amount: Huf | None = None,
) -> LogEntry:
    return LogEntry.objects.create(
        customer=customer,
        plan=plan,
        event=event,
        message=message,
        mandate_version=mandate_version,
        clause=clause,
        amount=amount,
        created_at=clock.now(),
    )


def transactions_of(customer: User) -> list[Txn]:
    return [t.to_rule() for t in Transaction.objects.filter(account__customer=customer)]


def _active_products() -> list[ProductInfo]:
    return [p.to_rule() for p in Product.objects.filter(active=True)]


def _expenses(answer: QuestionnaireAnswer) -> list[PlannedExpense]:
    return [PlannedExpense(e.name, e.amount, e.due_on) for e in answer.expenses.all()]


def submit_questionnaire(
    customer: User,
    *,
    risk_score: int,
    existing_emergency_fund: Huf,
    expected_monthly_savings: Huf | None,
    planned_expenses: Sequence[PlannedExpense],
    clock: Clock,
) -> QuestionnaireAnswer:
    """Store the fixed questionnaire. Rejects past expense dates and non-positive amounts (AC8)."""
    today = clock.today()
    for index, expense in enumerate(planned_expenses):
        if expense.amount <= 0:
            raise InvalidInput(
                f"The amount of '{expense.name}' must be positive.",
                f"planned_expenses.{index}.amount",
            )
        if expense.due_on < today:
            raise InvalidInput(
                f"The due date of '{expense.name}' ({expense.due_on}) is in the past.",
                f"planned_expenses.{index}.due_on",
            )
    if existing_emergency_fund < 0:
        raise InvalidInput(
            "The existing emergency fund cannot be negative.", "existing_emergency_fund"
        )
    if expected_monthly_savings is not None and expected_monthly_savings <= 0:
        raise InvalidInput(
            "The expected monthly savings must be positive.", "expected_monthly_savings"
        )
    with transaction.atomic():
        answer = QuestionnaireAnswer.objects.create(
            customer=customer,
            risk_score=risk_score,
            existing_emergency_fund=existing_emergency_fund,
            expected_monthly_savings=expected_monthly_savings,
            submitted_at=clock.now(),
        )
        ExpenseAnswer.objects.bulk_create(
            [
                ExpenseAnswer(questionnaire=answer, name=e.name, amount=e.amount, due_on=e.due_on)
                for e in planned_expenses
            ]
        )
    return answer


def analyse(customer: User, clock: Clock) -> tuple[SurplusAnalysis, Confidence]:
    params = RuleConfig.load()
    analysis = analyse_surplus(transactions_of(customer), clock.today(), params)
    return analysis, assess_confidence(analysis.months_of_data, params)


def _save_items(plan: Plan, items: Sequence[PlanItemDraft]) -> None:
    PlanItem.objects.bulk_create(
        [
            PlanItem(
                plan=plan,
                position=position,
                kind=draft.kind.value,
                label=draft.label,
                product_id=draft.product.id,
                monthly_amount=draft.monthly_amount,
                target_amount=draft.target_amount,
            )
            for position, draft in enumerate(items)
        ]
    )


def propose_plan(customer: User, clock: Clock) -> tuple[Proposal, Plan | None]:
    """Run the rule engine on the latest questionnaire. Stores a Plan only for Outcome.PLAN."""
    answer = (
        QuestionnaireAnswer.objects.filter(customer=customer)
        .order_by("-submitted_at", "-id")
        .first()
    )
    if answer is None:
        raise PlanConflict("Please fill in the questionnaire first.")
    params = RuleConfig.load()
    inputs = PlanInputs(
        today=clock.today(),
        risk_score=answer.risk_score,
        existing_emergency_fund=answer.existing_emergency_fund,
        expected_monthly_savings=answer.expected_monthly_savings,
        planned_expenses=_expenses(answer),
        transactions=transactions_of(customer),
    )
    try:
        proposal = propose(inputs, _active_products(), params)
    except NoEligibleProduct as error:
        raise PlanConflict(str(error)) from error
    if proposal.outcome is not Outcome.PLAN:
        log_event(customer, proposal.outcome.value, "No plan was created.", clock)
        return proposal, None
    with transaction.atomic():
        plan = Plan.objects.create(
            customer=customer,
            questionnaire=answer,
            monthly_amount=proposal.monthly_amount,
            proposed_amount=proposal.monthly_amount,
            median_surplus=proposal.analysis.median_surplus,
            median_expenses=proposal.analysis.median_expenses,
            months_of_data=proposal.analysis.months_of_data,
            confidence=proposal.confidence.value,
            created_at=clock.now(),
        )
        _save_items(plan, proposal.items)
        log_event(
            customer,
            "plan_proposed",
            f"Plan {plan.pk} proposed: {proposal.monthly_amount} HUF a month.",
            clock,
            plan=plan,
            amount=proposal.monthly_amount,
        )
    return proposal, plan


def get_owned_plan(customer: User, plan_id: int) -> Plan:
    """Fetch by id, then check the owner: another customer's plan is 403, not 404 (AC8)."""
    plan = Plan.objects.filter(pk=plan_id).first()
    if plan is None:
        raise Http404("Plan not found.")
    if plan.customer_id != customer.pk:
        raise PermissionDenied("This plan belongs to another customer.")
    return plan


def accept_plan(plan: Plan, clock: Clock) -> list[RecurringOrder]:
    """Sign mandate version N+1 and create one recurring order per item, exactly once (AC7)."""
    with transaction.atomic():
        plan = Plan.objects.select_for_update().get(pk=plan.pk)
        if plan.status == Plan.Status.ACCEPTED:
            return list(RecurringOrder.objects.filter(plan_item__plan=plan).order_by("id"))
        if plan.status != Plan.Status.PROPOSED:
            raise PlanConflict(f"A {plan.status} plan cannot be accepted.")
        active = (
            Plan.objects.select_for_update()
            .filter(customer_id=plan.customer_id, status=Plan.Status.ACCEPTED)
            .first()
        )
        if active is not None and active.pk != plan.revises_id:
            raise PlanConflict("Pause your active plan before accepting a new one.")
        if active is not None:  # signing a revision replaces the plan it revises (ADR-0004)
            pause_plan(active, clock)
        items = list(plan.items.select_related("product"))
        latest = Mandate.objects.filter(customer_id=plan.customer_id).aggregate(v=Max("version"))
        version = (latest["v"] or 0) + 1
        mandate = Mandate.objects.create(
            customer_id=plan.customer_id,
            plan=plan,
            version=version,
            max_monthly_amount=plan.monthly_amount,
            min_balance=RuleConfig.load().min_balance,
            per_transfer_approval=plan.per_transfer_approval,
            signed_at=clock.now(),
        )
        mandate.products.set({item.product_id for item in items})
        orders = [
            RecurringOrder.objects.create(
                plan_item=item,
                mandate=mandate,
                product=item.product,
                monthly_amount=item.monthly_amount,
            )
            for item in items
        ]
        plan.status = Plan.Status.ACCEPTED
        plan.save(update_fields=["status"])
        log_event(
            plan.customer,
            "plan_accepted",
            f"Plan {plan.pk} accepted; mandate v{version} signed; {len(orders)} orders created.",
            clock,
            plan=plan,
            mandate_version=version,
            amount=plan.monthly_amount,
        )
    return orders


def reject_plan(plan: Plan, clock: Clock) -> Plan:
    """A rejected plan never creates orders (AC7)."""
    plan.refresh_from_db()  # the caller's copy may predate an accept or pause
    if plan.status == Plan.Status.REJECTED:
        return plan
    if plan.status != Plan.Status.PROPOSED:
        raise PlanConflict(f"A {plan.status} plan cannot be rejected.")
    plan.status = Plan.Status.REJECTED
    plan.save(update_fields=["status"])
    log_event(plan.customer, "plan_rejected", f"Plan {plan.pk} rejected.", clock, plan=plan)
    return plan


def _allocate(plan: Plan, monthly_amount: Huf, clock: Clock) -> list[PlanItemDraft]:
    """Re-run the priority allocation for `plan`'s questionnaire with a new amount."""
    if not 0 < monthly_amount <= plan.proposed_amount:
        raise InvalidInput(
            f"The monthly amount must be between 1 and {plan.proposed_amount} HUF.",
            "monthly_amount",
        )
    answer = plan.questionnaire
    try:
        return list(
            allocate(
                monthly_amount,
                median_expenses=plan.median_expenses,
                risk_score=answer.risk_score,
                existing_emergency_fund=answer.existing_emergency_fund,
                planned_expenses=_expenses(answer),
                today=clock.today(),
                products=_active_products(),
                params=RuleConfig.load(),
            )
        )
    except NoEligibleProduct as error:
        raise PlanConflict(str(error)) from error


def edit_amount(plan: Plan, monthly_amount: Huf, clock: Clock) -> Plan:
    """Lower the amount of a proposed plan and re-run the allocation. Nothing executes until
    the revised plan is accepted."""
    plan.refresh_from_db()
    if plan.status != Plan.Status.PROPOSED:
        raise PlanConflict("Only a proposed plan can be edited.")
    items = _allocate(plan, monthly_amount, clock)
    with transaction.atomic():
        plan.items.all().delete()
        _save_items(plan, items)
        plan.monthly_amount = monthly_amount
        plan.save(update_fields=["monthly_amount"])
        log_event(
            plan.customer,
            "plan_edited",
            f"Plan {plan.pk} amount set to {monthly_amount} HUF a month.",
            clock,
            plan=plan,
            amount=monthly_amount,
        )
    return plan


def revise_plan(plan: Plan, monthly_amount: Huf, clock: Clock) -> Plan:
    """Propose a new amount for an accepted plan (ADR-0004). The accepted plan keeps running
    until the revision is signed; accept_plan then pauses it."""
    plan.refresh_from_db()
    if plan.status != Plan.Status.ACCEPTED:
        raise PlanConflict("Only an active plan can be revised.")
    if plan.revisions.filter(status=Plan.Status.PROPOSED).exists():
        raise PlanConflict("A revised plan is already waiting for your signature.")
    items = _allocate(plan, monthly_amount, clock)
    with transaction.atomic():
        revision = Plan.objects.create(
            customer_id=plan.customer_id,
            questionnaire=plan.questionnaire,
            revises=plan,
            monthly_amount=monthly_amount,
            proposed_amount=plan.proposed_amount,
            median_surplus=plan.median_surplus,
            median_expenses=plan.median_expenses,
            months_of_data=plan.months_of_data,
            confidence=plan.confidence,
            created_at=clock.now(),
        )
        _save_items(revision, items)
        log_event(
            plan.customer,
            "plan_revised",
            f"Plan {revision.pk} proposed to replace plan {plan.pk}: {monthly_amount} HUF a month.",
            clock,
            plan=revision,
            amount=monthly_amount,
        )
    return revision


def pause_plan(plan: Plan, clock: Clock) -> Plan:
    """Pause an accepted plan: its mandate and orders stop (mandate clause 4)."""
    plan.refresh_from_db()  # the caller's copy may predate an accept or pause
    if plan.status == Plan.Status.PAUSED:
        return plan
    if plan.status != Plan.Status.ACCEPTED:
        raise PlanConflict("Only an active plan can be paused.")
    with transaction.atomic():
        plan.status = Plan.Status.PAUSED
        plan.save(update_fields=["status"])
        mandate = Mandate.objects.get(plan=plan)
        mandate.status = Mandate.Status.PAUSED
        mandate.save(update_fields=["status"])
        RecurringOrder.objects.filter(mandate=mandate).update(status=RecurringOrder.Status.PAUSED)
        log_event(
            plan.customer,
            "plan_paused",
            f"Plan {plan.pk} paused.",
            clock,
            plan=plan,
            mandate_version=mandate.version,
            clause=PAUSE_CLAUSE,
        )
    return plan


def active_plan(customer: User) -> Plan | None:
    return (
        Plan.objects.filter(
            customer=customer, status__in=[Plan.Status.ACCEPTED, Plan.Status.PAUSED]
        )
        .order_by("-created_at", "-id")
        .first()
    )


def time_machine(plan: Plan, clock: Clock) -> BacktestResult:
    """Replay the plan's monthly amount on the customer's own history (AC4)."""
    account = Account.objects.filter(customer_id=plan.customer_id).first()
    if account is None:
        raise PlanConflict("No account found for this customer.")
    return backtest(
        transactions_of(plan.customer),
        account.balance,
        plan.monthly_amount,
        clock.today(),
        RuleConfig.load(),
    )


def item_saved_amounts(plan: Plan) -> dict[int, Huf]:
    """Saved so far per plan item (by PlanItem pk): executed transfers of all the customer's
    orders with the same item kind and label, so a revised plan continues the same pot. The
    emergency fund also counts the fund the customer already had (questionnaire)."""
    rows = (
        Execution.objects.filter(
            order__mandate__customer_id=plan.customer_id, status=Execution.Status.EXECUTED
        )
        .values("order__plan_item__kind", "order__plan_item__label")
        .annotate(total=Sum("amount"))
    )
    executed = {
        (r["order__plan_item__kind"], r["order__plan_item__label"]): r["total"] for r in rows
    }
    # ponytail: a later questionnaire that already includes SaverAI transfers in its emergency
    # fund counts them twice; track pots per customer if questionnaires are re-taken often.
    existing = plan.questionnaire.existing_emergency_fund
    return {
        item.pk: executed.get((item.kind, item.label), 0)
        + (existing if item.kind == ItemKind.EMERGENCY_FUND else 0)
        for item in plan.items.all()
    }


def plan_saved_total(plan: Plan) -> Huf:
    """Executed transfers of this plan's orders ("Saved by SaverAI")."""
    total = Execution.objects.filter(
        order__plan_item__plan=plan, status=Execution.Status.EXECUTED
    ).aggregate(total=Sum("amount"))["total"]
    return total or 0
