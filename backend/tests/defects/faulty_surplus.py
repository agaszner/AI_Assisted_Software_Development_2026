"""DELIBERATE DEFECT (homework): AC1 surplus computed with the MEAN instead of the MEDIAN.

Copy of rules.surplus.analyse_surplus with one changed line (marked below). Do not fix.
The fixed version is the real backend/rules/surplus.py.
"""

from collections.abc import Sequence
from datetime import date

from rules.defaults import DEFAULTS, RuleParams
from rules.money import Huf, median, percent_of
from rules.surplus import SurplusAnalysis, complete_months, month_flows
from rules.types import Txn


def analyse_surplus(
    transactions: Sequence[Txn], today: date, params: RuleParams = DEFAULTS
) -> SurplusAnalysis:
    months = complete_months(transactions, today)
    flows = month_flows(transactions, months[-params.surplus_window_months :])
    median_expenses = median([f.expenses for f in flows]) if flows else 0
    if len(months) < params.min_months_for_estimate:
        return SurplusAnalysis(len(months), flows, None, median_expenses, None)
    surplus: Huf = sum(f.surplus for f in flows) // len(flows)  # DEFECT: mean, not median
    amount = percent_of(surplus, params.monthly_share_percent) if surplus > 0 else 0
    return SurplusAnalysis(len(months), flows, surplus, median_expenses, amount)
