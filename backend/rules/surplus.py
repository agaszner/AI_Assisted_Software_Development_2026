"""Monthly surplus and suggested monthly amount (AC1, AC5; AC6 "no estimate")."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from rules.defaults import DEFAULTS, RuleParams
from rules.money import Huf, median, percent_of
from rules.months import add_months, month_of, months_between
from rules.types import Txn


@dataclass(frozen=True)
class MonthFlow:
    month: date  # first day of the calendar month
    income: Huf
    expenses: Huf  # positive number

    @property
    def surplus(self) -> Huf:
        return self.income - self.expenses


@dataclass(frozen=True)
class SurplusAnalysis:
    months_of_data: int
    flows: tuple[MonthFlow, ...]  # the analysed window, oldest first
    median_surplus: Huf | None  # None: too little data for an estimate (AC6)
    median_expenses: Huf  # 0 when there is no data
    monthly_amount: Huf | None  # None: no estimate (AC6); 0: no surplus (AC5)


def complete_months(transactions: Sequence[Txn], today: date) -> list[date]:
    """Calendar months from the first counted transaction up to the month before `today`."""
    current = month_of(today)
    booked = [
        month_of(t.booked_on)
        for t in transactions
        if not t.own_transfer and month_of(t.booked_on) < current
    ]
    if not booked:
        return []
    first = min(booked)
    return [add_months(first, i) for i in range(months_between(first, current))]


def month_flows(transactions: Sequence[Txn], months: Sequence[date]) -> tuple[MonthFlow, ...]:
    income = dict.fromkeys(months, 0)
    expenses = dict.fromkeys(months, 0)
    for t in transactions:
        month = month_of(t.booked_on)
        if t.own_transfer or month not in income:
            continue
        if t.amount >= 0:
            income[month] += t.amount
        else:
            expenses[month] -= t.amount
    return tuple(MonthFlow(m, income[m], expenses[m]) for m in months)


def analyse_surplus(
    transactions: Sequence[Txn], today: date, params: RuleParams = DEFAULTS
) -> SurplusAnalysis:
    """Median surplus of the last complete months and the suggested monthly amount.

    Inputs: the customer's transactions, today's date (from the Clock), rule parameters.
    Output: monthly_amount = monthly_share_percent % of the median surplus of the last
    surplus_window_months complete months (AC1); 0 if that median is not positive (AC5);
    None if fewer than min_months_for_estimate months exist (AC6).
    """
    months = complete_months(transactions, today)
    flows = month_flows(transactions, months[-params.surplus_window_months :])
    median_expenses = median([f.expenses for f in flows]) if flows else 0
    if len(months) < params.min_months_for_estimate:
        return SurplusAnalysis(len(months), flows, None, median_expenses, None)
    median_surplus = median([f.surplus for f in flows])
    amount = percent_of(median_surplus, params.monthly_share_percent) if median_surplus > 0 else 0
    return SurplusAnalysis(len(months), flows, median_surplus, median_expenses, amount)
