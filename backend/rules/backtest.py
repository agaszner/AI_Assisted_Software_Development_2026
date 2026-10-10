"""Financial time machine: replay a plan on the customer's past transactions (AC4).

Shared contract for the dual implementation (AGENTS.md section 11): keep the signature of
`backtest` and the result dataclasses unchanged. Shows past behaviour only, not a forecast.
Principal only: no product returns, no inflation (ADR-0002).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from rules.defaults import DEFAULTS, RuleParams
from rules.money import Huf
from rules.months import add_months, month_of
from rules.types import Txn


@dataclass(frozen=True)
class BacktestMonth:
    month: date
    balance_before_transfer: Huf
    transfer: Huf  # 0 when skipped
    skipped: bool
    balance_after: Huf
    saved_to_date: Huf


@dataclass(frozen=True)
class BacktestResult:
    months: tuple[BacktestMonth, ...]
    total_saved: Huf
    skipped_months: tuple[date, ...]


def backtest(
    transactions: Sequence[Txn],
    current_balance: Huf,
    monthly_amount: Huf,
    today: date,
    params: RuleParams = DEFAULTS,
) -> BacktestResult:
    """Replay `monthly_amount` on the last `backtest_months` complete months.

    The opening balance is rebuilt backwards from `current_balance` (all transactions, own
    transfers included, move the balance). Each month: apply that month's transactions, then
    transfer at month end unless the balance would drop below `min_balance` → skipped (AC4).
    Months before the first transaction are left out.
    """
    if monthly_amount <= 0:
        raise ValueError("monthly_amount must be positive")
    current = month_of(today)
    window = [add_months(current, -n) for n in range(params.backtest_months, 0, -1)]
    if transactions:
        first_data = min(month_of(t.booked_on) for t in transactions)
        window = [m for m in window if m >= first_data]
    else:
        window = []
    if not window:
        return BacktestResult((), 0, ())

    balance = current_balance - sum(t.amount for t in transactions if t.booked_on >= window[0])
    saved = 0
    months: list[BacktestMonth] = []
    for month in window:
        balance += sum(t.amount for t in transactions if month_of(t.booked_on) == month)
        before = balance
        skipped = before - monthly_amount < params.min_balance
        transfer = 0 if skipped else monthly_amount
        balance -= transfer
        saved += transfer
        months.append(BacktestMonth(month, before, transfer, skipped, balance, saved))
    skipped_months = tuple(m.month for m in months if m.skipped)
    return BacktestResult(tuple(months), saved, skipped_months)
