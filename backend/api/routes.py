"""Customer endpoints. Plans and transfers are always loaded through the ownership checks in
plans.services / plans.execution, so another customer's data gives 403 (AC8)."""

from datetime import date

from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.http import Http404, HttpRequest
from ninja import Router, Status

from api.auth import current_user
from api.schemas import (
    AcceptIn,
    AccountOut,
    ActivityOut,
    AmountIn,
    AnalysisOut,
    BacktestMonthOut,
    ClauseOut,
    ExecutionOut,
    IdOut,
    MandateOut,
    MonthOut,
    PlanItemOut,
    PlanOut,
    ProductOut,
    ProposalOut,
    QuestionnaireIn,
    RulesOut,
    TimeMachineOut,
    TransactionOut,
)
from banking.models import Account, Product
from core.clock import get_clock
from plans import activity as activities
from plans import execution as executions
from plans import explanations, services
from plans.models import Execution, Mandate, Plan, RuleConfig
from rules.confidence import Confidence
from rules.mandate import CLAUSES
from rules.money import progress_percent
from rules.months import next_transfer_on
from rules.plan import ItemKind, Outcome, Proposal
from rules.types import PlannedExpense

router = Router(tags=["customer"])

# Display limit for the home screen (Figma 02 shows five), not a rule parameter.
RECENT_TRANSACTIONS = 5


def product_out(product: Product) -> ProductOut:
    return ProductOut(
        id=product.pk, name=product.name, risk_level=product.risk_level, liquid=product.liquid
    )


def plan_out(plan: Plan) -> PlanOut:
    params = RuleConfig.load()
    mandate = Mandate.objects.filter(plan=plan).first()
    saved = services.item_saved_amounts(plan)
    # ponytail: two expenses with the same name share the first due date; store due_on on
    # PlanItem if that ever matters.
    due_dates: dict[str, date] = {}
    for expense in plan.questionnaire.expenses.order_by("due_on"):
        due_dates.setdefault(expense.name, expense.due_on)
    items = [
        PlanItemOut(
            position=item.position,
            kind=item.kind,
            label=item.label,
            product=product_out(item.product),
            monthly_amount=item.monthly_amount,
            target_amount=item.target_amount,
            due_on=due_dates.get(item.label) if item.kind == ItemKind.PLANNED_EXPENSE else None,
            saved_amount=saved[item.pk],
            progress_percent=(
                progress_percent(saved[item.pk], item.target_amount) if item.target_amount else None
            ),
        )
        for item in plan.items.select_related("product")
    ]
    return PlanOut(
        id=plan.pk,
        status=plan.status,
        revises=plan.revises_id,
        pending_revision=plan.revisions.filter(status=Plan.Status.PROPOSED)
        .values_list("pk", flat=True)
        .first(),
        created_on=plan.created_at.date(),
        monthly_amount=plan.monthly_amount,
        proposed_amount=plan.proposed_amount,
        median_surplus=plan.median_surplus,
        months_of_data=plan.months_of_data,
        share_percent=params.monthly_share_percent,
        risk_score=plan.questionnaire.risk_score,
        min_balance=mandate.min_balance if mandate else params.min_balance,
        confidence=plan.confidence,
        per_transfer_approval=plan.per_transfer_approval,
        next_transfer_on=next_transfer_on(get_clock().today()),
        mandate_version=mandate.version if mandate else None,
        signed_on=mandate.signed_at.date() if mandate else None,
        saved_total=services.plan_saved_total(plan),
        items=items,
        explanations=explanations.plan_summary(
            amount=plan.monthly_amount,
            median_surplus=plan.median_surplus,
            percent=params.monthly_share_percent,
            months_of_data=plan.months_of_data,
            confidence=Confidence(plan.confidence),
        ),
    )


def no_plan_explanations(proposal: Proposal) -> list[str]:
    analysis = proposal.analysis
    if proposal.outcome is Outcome.NO_SURPLUS:
        return [explanations.no_surplus(len(analysis.flows), analysis.median_surplus or 0)]
    required = RuleConfig.load().min_months_for_estimate
    return [explanations.needs_expected_savings(analysis.months_of_data, required)]


def execution_out(execution: Execution) -> ExecutionOut:
    return ExecutionOut(
        id=execution.pk,
        period=execution.period,
        status=execution.status,
        amount=execution.amount,
        mandate_version=execution.mandate_version,
        clause=execution.clause,
        reason=execution.reason,
    )


def owned_plan(request: HttpRequest, plan_id: int) -> Plan:
    return services.get_owned_plan(current_user(request), plan_id)


@router.post("/questionnaire", response={201: IdOut})
def submit_questionnaire(request: HttpRequest, payload: QuestionnaireIn) -> Status[IdOut]:
    answer = services.submit_questionnaire(
        current_user(request),
        risk_score=payload.risk_score,
        existing_emergency_fund=payload.existing_emergency_fund,
        expected_monthly_savings=payload.expected_monthly_savings,
        planned_expenses=[
            PlannedExpense(e.name, e.amount, e.due_on) for e in payload.planned_expenses
        ],
        clock=get_clock(),
    )
    return Status(201, IdOut(id=answer.pk))


@router.get("/analysis", response=AnalysisOut)
def analysis(request: HttpRequest) -> AnalysisOut:
    result, confidence = services.analyse(current_user(request), get_clock())
    params = RuleConfig.load()
    if result.median_surplus is None:
        notes = [
            explanations.needs_expected_savings(
                result.months_of_data, params.min_months_for_estimate
            )
        ]
    elif result.median_surplus <= 0:  # AC5 boundary, ADR-0002
        notes = [explanations.no_surplus(len(result.flows), result.median_surplus)]
    else:
        notes = []
    return AnalysisOut(
        months_of_data=result.months_of_data,
        confidence=confidence.value,
        median_surplus=result.median_surplus,
        median_expenses=result.median_expenses,
        monthly_amount=result.monthly_amount,
        share_percent=params.monthly_share_percent,
        median_explanation=(
            None
            if result.median_surplus is None
            else explanations.median_working(
                [f.surplus for f in result.flows], result.median_surplus
            )
        ),
        explanations=notes,
        months=[
            MonthOut(month=f.month, income=f.income, expenses=f.expenses, surplus=f.surplus)
            for f in result.flows
        ],
    )


@router.post("/plans", response=ProposalOut)
def propose_plan(request: HttpRequest) -> ProposalOut:
    proposal, plan = services.propose_plan(current_user(request), get_clock())
    if plan is None:
        return ProposalOut(
            outcome=proposal.outcome.value, plan=None, explanations=no_plan_explanations(proposal)
        )
    out = plan_out(plan)
    return ProposalOut(outcome=proposal.outcome.value, plan=out, explanations=out.explanations)


@router.get("/plans/active", response=PlanOut)
def get_active_plan(request: HttpRequest) -> PlanOut:
    plan = services.active_plan(current_user(request))
    if plan is None:
        raise Http404("No active plan.")
    return plan_out(plan)


@router.get("/plans/{plan_id}", response=PlanOut)
def get_plan(request: HttpRequest, plan_id: int) -> PlanOut:
    return plan_out(owned_plan(request, plan_id))


@router.patch("/plans/{plan_id}", response=PlanOut)
def edit_plan(request: HttpRequest, plan_id: int, payload: AmountIn) -> PlanOut:
    plan = services.edit_amount(owned_plan(request, plan_id), payload.monthly_amount, get_clock())
    return plan_out(plan)


@router.get("/plans/{plan_id}/time-machine", response=TimeMachineOut)
def time_machine(request: HttpRequest, plan_id: int) -> TimeMachineOut:
    result = services.time_machine(owned_plan(request, plan_id), get_clock())
    minimum = RuleConfig.load().min_balance
    return TimeMachineOut(
        total_saved=result.total_saved,
        months_replayed=len(result.months),
        transfers_made=sum(1 for m in result.months if not m.skipped),
        skipped_months=list(result.skipped_months),
        months=[
            BacktestMonthOut(
                month=m.month,
                balance_before_transfer=m.balance_before_transfer,
                transfer=m.transfer,
                skipped=m.skipped,
                balance_after=m.balance_after,
                saved_to_date=m.saved_to_date,
                note=explanations.skipped_month(m.month, minimum) if m.skipped else None,
            )
            for m in result.months
        ],
    )


@router.post("/plans/{plan_id}/accept", response=PlanOut)
def accept_plan(request: HttpRequest, plan_id: int, payload: AcceptIn) -> PlanOut:
    """Sign the mandate (AC7). The password confirms the signature (simulated strong customer
    authentication, ADR-0004). Ownership is checked first, so another customer's plan is 403
    whatever the password (AC8)."""
    plan = owned_plan(request, plan_id)
    if not current_user(request).check_password(payload.password):
        raise PermissionDenied("Incorrect password.")
    services.accept_plan(plan, get_clock())
    plan.refresh_from_db()
    return plan_out(plan)


@router.post("/plans/{plan_id}/revise", response=PlanOut)
def revise_plan(request: HttpRequest, plan_id: int, payload: AmountIn) -> PlanOut:
    """Propose a new amount for the active plan; nothing changes until it is signed (ADR-0004)."""
    return plan_out(
        services.revise_plan(owned_plan(request, plan_id), payload.monthly_amount, get_clock())
    )


@router.post("/plans/{plan_id}/reject", response=PlanOut)
def reject_plan(request: HttpRequest, plan_id: int) -> PlanOut:
    return plan_out(services.reject_plan(owned_plan(request, plan_id), get_clock()))


@router.post("/plans/{plan_id}/pause", response=PlanOut)
def pause_plan(request: HttpRequest, plan_id: int) -> PlanOut:
    return plan_out(services.pause_plan(owned_plan(request, plan_id), get_clock()))


@router.get("/executions", response=list[ExecutionOut])
def list_executions(request: HttpRequest) -> list[ExecutionOut]:
    rows = Execution.objects.filter(order__mandate__customer=current_user(request)).order_by(
        "-period", "id"
    )
    return [execution_out(e) for e in rows]


@router.post("/executions/{execution_id}/approve", response=ExecutionOut)
def approve_execution(request: HttpRequest, execution_id: int) -> ExecutionOut:
    execution = executions.get_owned_execution(current_user(request), execution_id)
    return execution_out(executions.approve_execution(execution, get_clock()))


@router.get("/account", response=AccountOut)
def get_account(request: HttpRequest) -> AccountOut:
    """Balance and the newest transactions up to today (home screen)."""
    account = Account.objects.filter(customer=current_user(request)).first()
    if account is None:
        raise Http404("No account found.")
    today = get_clock().today()
    rows = account.transactions.filter(booked_on__lte=today).order_by("-booked_on", "-id")[
        :RECENT_TRANSACTIONS
    ]
    return AccountOut(
        today=today,
        name=account.name,
        balance=account.balance,
        min_balance=RuleConfig.load().min_balance,
        transactions=[
            TransactionOut(
                id=t.pk,
                booked_on=t.booked_on,
                amount=t.amount,
                description=t.description,
                own_transfer=t.own_transfer,
            )
            for t in rows
        ],
    )


@router.get("/rules", response=RulesOut)
def get_rules(request: HttpRequest) -> RulesOut:
    """The plan rules in words, filled from RuleConfig (Home: "How the plan is calculated")."""
    return RulesOut(lines=explanations.rule_lines(RuleConfig.load()))


@router.get("/plans/{plan_id}/mandate", response=MandateOut)
def get_mandate(request: HttpRequest, plan_id: int) -> MandateOut:
    """The signed mandate of an accepted plan, or a preview of the terms that accepting signs."""
    plan = owned_plan(request, plan_id)
    clauses = [ClauseOut(number=number, text=text) for number, text in sorted(CLAUSES.items())]
    signed = Mandate.objects.filter(plan=plan).first()
    if signed is not None:
        return MandateOut(
            status=signed.status,
            version=signed.version,
            signed_at=signed.signed_at,
            max_monthly_amount=signed.max_monthly_amount,
            min_balance=signed.min_balance,
            per_transfer_approval=signed.per_transfer_approval,
            products=[product_out(p) for p in signed.products.order_by("risk_level", "id")],
            clauses=clauses,
        )
    # Same terms as services.accept_plan signs
    # (pinned by test_mandate_preview_matches_signed_mandate).
    products = {item.product.pk: item.product for item in plan.items.select_related("product")}
    latest = Mandate.objects.filter(customer_id=plan.customer_id).aggregate(v=Max("version"))["v"]
    return MandateOut(
        status="unsigned",
        version=(latest or 0) + 1,  # same rule as services.accept_plan
        signed_at=None,
        max_monthly_amount=plan.monthly_amount,
        min_balance=RuleConfig.load().min_balance,
        per_transfer_approval=plan.per_transfer_approval,
        products=[
            product_out(p) for p in sorted(products.values(), key=lambda p: (p.risk_level, p.pk))
        ],
        clauses=clauses,
    )


@router.get("/activity", response=list[ActivityOut])
def list_activity(request: HttpRequest) -> list[ActivityOut]:
    """The customer's execution log (Figma 08 and Activity): only their own rows (AC8)."""
    rows = activities.activity(current_user(request), get_clock())
    return [ActivityOut(**vars(row)) for row in rows]
