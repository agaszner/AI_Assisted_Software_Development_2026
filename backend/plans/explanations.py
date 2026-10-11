"""Fixed explanation templates (golden rule 2). They only format rule-engine results;
they never compute amounts, dates or decisions."""

from collections.abc import Sequence
from datetime import date

from rules.confidence import Confidence
from rules.defaults import RuleParams
from rules.money import Huf, middle_values

NO_SURPLUS = (
    "Your median monthly surplus over the last {months} months is {median} HUF, so there is "
    "no surplus to save. No investment plan was created."
)
NEEDS_EXPECTED_SAVINGS = (
    "We found only {months} full months of transactions; at least {required} are needed for an "
    "estimate. Please enter how much you expect to save each month."
)
PLAN_FROM_SURPLUS = (
    "We suggest saving {amount} HUF a month: {percent}% of your median monthly surplus of "
    "{median} HUF."
)
PLAN_FROM_EXPECTED = (
    "We suggest saving {amount} HUF a month, the amount you said you expect to save."
)
LOW_CONFIDENCE = (
    "This plan is based on only {months} months of data, so its confidence is low. "
    "Every transfer will ask for your approval."
)
SKIPPED_MONTH = (
    "{month}: the transfer was skipped because it would have left less than {minimum} HUF "
    "on your account."
)


def huf(amount: Huf) -> str:
    return f"{amount:,}"


def no_surplus(months: int, median: Huf) -> str:
    return NO_SURPLUS.format(months=months, median=huf(median))


def needs_expected_savings(months: int, required: int) -> str:
    return NEEDS_EXPECTED_SAVINGS.format(months=months, required=required)


def plan_summary(
    *,
    amount: Huf,
    median_surplus: Huf | None,
    percent: int,
    months_of_data: int,
    confidence: Confidence,
) -> list[str]:
    if median_surplus is None:
        lines = [PLAN_FROM_EXPECTED.format(amount=huf(amount))]
    else:
        lines = [
            PLAN_FROM_SURPLUS.format(
                amount=huf(amount), percent=percent, median=huf(median_surplus)
            )
        ]
    if confidence is not Confidence.NORMAL:
        lines.append(LOW_CONFIDENCE.format(months=months_of_data))
    return lines


def skipped_month(month: date, minimum: Huf) -> str:
    return SKIPPED_MONTH.format(month=f"{month:%Y-%m}", minimum=huf(minimum))


RULE_LINES = (
    "Monthly amount = {percent}% of your median monthly surplus (last {window} months).",
    "Priority: emergency fund ({fund_months}× median monthly expenses), then planned expenses, "
    "then long-term investment.",
    "Money needed within {liquid_months} months goes only to low-risk, liquid products.",
    "A transfer is skipped if it would leave less than {minimum} HUF on your account.",
)


def rule_lines(params: RuleParams) -> list[str]:
    values = {
        "percent": params.monthly_share_percent,
        "window": params.surplus_window_months,
        "fund_months": params.emergency_fund_months,
        "liquid_months": params.liquid_horizon_months,
        "minimum": huf(params.min_balance),
    }
    return [line.format(**values) for line in RULE_LINES]


MEDIAN_EVEN = "Sorted: {values}. Median = ({low} + {high}) / 2 = {median} HUF."
MEDIAN_ODD = "Sorted: {values}. Median = {median} HUF."


def median_working(values: Sequence[Huf], median: Huf) -> str:
    """How the rule engine's median follows from the monthly surpluses (04 Spending analysis)."""
    listed = " · ".join(huf(v) for v in sorted(values))
    middle = middle_values(values)
    if len(middle) == 1:
        return MEDIAN_ODD.format(values=listed, median=huf(median))
    return MEDIAN_EVEN.format(
        values=listed, low=huf(middle[0]), high=huf(middle[1]), median=huf(median)
    )


TRANSFER_TITLES = {
    "emergency_fund": "{amount} HUF to your emergency fund",
    "planned_expense": "{amount} HUF to your {label} savings",
    "investment": "{amount} HUF to long-term investment",
}
EVENT_TITLES = {
    "plan_proposed": "Plan proposed: {amount} HUF a month",
    "plan_revised": "New amount proposed: {amount} HUF a month",
    "plan_edited": "Plan amount changed to {amount} HUF a month",
    "plan_accepted": (
        "You accepted the plan and signed mandate version {version}: {orders} monthly "
        "transfers set up"
    ),
    "plan_rejected": "You rejected the plan",
    "plan_paused": "Plan paused: mandate version {version} stopped (§4)",
}
SCHEDULED_CHECK = "Will be checked against {clauses}"
DECISION = "§{clause} · {reason}"


def transfer_title(kind: str, label: str, amount: Huf) -> str:
    return TRANSFER_TITLES[kind].format(amount=huf(amount), label=label)


def event_title(event: str, *, amount: Huf | None, version: int | None, orders: int) -> str | None:
    """Customer-facing title of a log event; None for events the activity feed does not show
    (executions appear as their own rows)."""
    template = EVENT_TITLES.get(event)
    if template is None:
        return None
    return template.format(amount=huf(amount or 0), version=version, orders=orders)


def scheduled_check(per_transfer_approval: bool) -> str:
    return SCHEDULED_CHECK.format(clauses="§1, §2 and §3" if per_transfer_approval else "§1 and §2")


def decision_text(clause: int, reason: str) -> str:
    return DECISION.format(clause=clause, reason=reason)
