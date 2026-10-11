"""Request and response schemas. Money and scores are strict ints: floats, strings and booleans
are rejected with 422 (golden rule 3, AC8). Past-date checks need the Clock, so they live in
plans.services.submit_questionnaire."""

from datetime import date, datetime
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
    share_percent: int
    median_explanation: str | None
    explanations: list[str]  # no-surplus (AC5) or too-little-data (AC6) message, else empty
    months: list[MonthOut]


class ProductOut(Schema):
    id: int
    name: str
    risk_level: int
    liquid: bool


class PlanItemOut(Schema):
    position: int
    kind: str
    label: str
    product: ProductOut
    monthly_amount: int
    target_amount: int | None
    due_on: date | None  # planned expenses only
    saved_amount: int
    progress_percent: int | None  # None when the item has no target


class PlanOut(Schema):
    id: int
    status: str
    revises: int | None  # the accepted plan this one would replace (ADR-0004)
    pending_revision: int | None  # a proposed revision of this plan waiting for signature
    created_on: date
    monthly_amount: int
    proposed_amount: int
    median_surplus: int | None
    months_of_data: int
    share_percent: int
    risk_score: int
    min_balance: int
    confidence: str
    per_transfer_approval: bool
    next_transfer_on: date
    mandate_version: int | None
    signed_on: date | None
    saved_total: int
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
    months_replayed: int
    transfers_made: int
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


class TransactionOut(Schema):
    id: int
    booked_on: date
    amount: int
    description: str
    own_transfer: bool


class AccountOut(Schema):
    today: date  # the server's Clock (honours SAVERAI_FIXED_DATE); the UI never reads its own clock
    name: str
    balance: int
    min_balance: int
    transactions: list[TransactionOut]


class RulesOut(Schema):
    lines: list[str]


class ClauseOut(Schema):
    number: int
    text: str


class MandateOut(Schema):
    status: str  # "unsigned" (plan only proposed), "active" or "paused"
    version: int  # unsigned: the version that accepting will sign
    signed_at: datetime | None
    max_monthly_amount: int
    min_balance: int
    per_transfer_approval: bool
    products: list[ProductOut]
    clauses: list[ClauseOut]


class AcceptIn(Schema):
    password: str = Field(min_length=1, max_length=128)


class ActivityOut(Schema):
    key: str
    on: date
    title: str
    amount: int | None
    status: str
    mandate_version: int | None
    clause: str | None
    idempotency_key: str | None
    logged_at: datetime | None
    execution_id: int | None
