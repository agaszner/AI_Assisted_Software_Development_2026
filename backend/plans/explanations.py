"""Fixed explanation templates (golden rule 2). They only format rule-engine results;
they never compute amounts, dates or decisions."""

from datetime import date

from rules.confidence import Confidence
from rules.money import Huf

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
