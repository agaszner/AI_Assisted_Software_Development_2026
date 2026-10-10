"""Customer endpoints. Plans and transfers are always loaded through the ownership checks in
plans.services / plans.execution, so another customer's data gives 403 (AC8)."""

from django.http import Http404, HttpRequest
from ninja import Router, Status

from api.auth import current_user
from api.schemas import (
    AmountIn,
    AnalysisOut,
    BacktestMonthOut,
    ExecutionOut,
    IdOut,
    MonthOut,
    PlanItemOut,
    PlanOut,
    ProductOut,
    ProposalOut,
    QuestionnaireIn,
    TimeMachineOut,
)
from core.clock import get_clock
from plans import execution as executions
from plans import explanations, services
from plans.models import Execution, Plan, RuleConfig
from rules.confidence import Confidence
from rules.plan import Outcome, Proposal
from rules.types import PlannedExpense

router = Router(tags=["customer"])


def plan_out(plan: Plan) -> PlanOut:
    params = RuleConfig.load()
    items = [
        PlanItemOut(
            kind=item.kind,
            label=item.label,
            product=ProductOut(
                id=item.product.pk,
                name=item.product.name,
                risk_level=item.product.risk_level,
                liquid=item.product.liquid,
            ),
            monthly_amount=item.monthly_amount,
            target_amount=item.target_amount,
        )
        for item in plan.items.select_related("product")
    ]
    return PlanOut(
        id=plan.pk,
        status=plan.status,
        monthly_amount=plan.monthly_amount,
        proposed_amount=plan.proposed_amount,
        confidence=plan.confidence,
        per_transfer_approval=plan.per_transfer_approval,
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
    return AnalysisOut(
        months_of_data=result.months_of_data,
        confidence=confidence.value,
        median_surplus=result.median_surplus,
        median_expenses=result.median_expenses,
        monthly_amount=result.monthly_amount,
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
def accept_plan(request: HttpRequest, plan_id: int) -> PlanOut:
    plan = owned_plan(request, plan_id)
    services.accept_plan(plan, get_clock())
    plan.refresh_from_db()
    return plan_out(plan)


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
