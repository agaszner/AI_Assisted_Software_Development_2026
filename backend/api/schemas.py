"""Request and response schemas. Money and scores are strict ints: floats, strings and booleans
are rejected with 422 (golden rule 3, AC8). Past-date checks need the Clock, so they live in
plans.services.submit_questionnaire."""

from datetime import date
from typing import Annotated

from ninja import Schema
from pydantic import Field

PositiveHuf = Annotated[int, Field(strict=True, gt=0)]
NonNegativeHuf = Annotated[int, Field(strict=True, ge=0)]
RiskScore = Annotated[int, Field(strict=True, ge=1, le=5)]


class ExpenseIn(Schema):
    name: str = Field(min_length=1, max_length=100)
    amount: PositiveHuf
    due_on: date


class QuestionnaireIn(Schema):
    risk_score: RiskScore
    existing_emergency_fund: NonNegativeHuf
    expected_monthly_savings: PositiveHuf | None = None
    planned_expenses: list[ExpenseIn] = Field(default_factory=list, max_length=10)


class AmountIn(Schema):
    monthly_amount: PositiveHuf


class IdOut(Schema):
    id: int


class MonthOut(Schema):
    month: date
    income: int
    expenses: int
    surplus: int


class AnalysisOut(Schema):
    months_of_data: int
    confidence: str
    median_surplus: int | None
    median_expenses: int
    monthly_amount: int | None
    months: list[MonthOut]


class ProductOut(Schema):
    id: int
    name: str
    risk_level: int
    liquid: bool


class PlanItemOut(Schema):
    kind: str
    label: str
    product: ProductOut
    monthly_amount: int
    target_amount: int | None


class PlanOut(Schema):
    id: int
    status: str
    monthly_amount: int
    proposed_amount: int
    confidence: str
    per_transfer_approval: bool
    items: list[PlanItemOut]
    explanations: list[str]


class ProposalOut(Schema):
    outcome: str
    plan: PlanOut | None
    explanations: list[str]


class BacktestMonthOut(Schema):
    month: date
    balance_before_transfer: int
    transfer: int
    skipped: bool
    balance_after: int
    saved_to_date: int
    note: str | None


class TimeMachineOut(Schema):
    total_saved: int
    skipped_months: list[date]
    months: list[BacktestMonthOut]


class ExecutionOut(Schema):
    id: int
    period: date
    status: str
    amount: int
    mandate_version: int
    clause: int
    reason: str
