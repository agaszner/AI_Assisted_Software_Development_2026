from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from rules.backtest import backtest
from rules.defaults import DEFAULTS
from rules.money import Huf
from rules.months import add_months
from rules.types import Txn
from tests.constants import TODAY

FIRST_MONTH = date(2025, 10, 1)  # 12 complete months before TODAY: Oct 2025 – Sep 2026


def steady_year(extra: list[Txn] | None = None, *, months: int = 12) -> list[Txn]:
    """Salary +400,000 and spending -400,000 every month: net 0."""
    start = add_months(FIRST_MONTH, 12 - months)
    txns: list[Txn] = []
    for i in range(months):
        month = add_months(start, i)
        txns += [Txn(month.replace(day=10), 400_000), Txn(month.replace(day=20), -400_000)]
    return txns + (extra or [])


def test_ac4_replays_twelve_months() -> None:
    result = backtest(steady_year(), current_balance=1_000_000, monthly_amount=50_000, today=TODAY)
    assert [m.month for m in result.months] == [add_months(FIRST_MONTH, i) for i in range(12)]
    assert result.total_saved == 600_000
    assert result.skipped_months == ()
    assert result.months[-1].balance_after == 400_000
    assert result.months[-1].saved_to_date == 600_000


def test_ac4_month_breaking_minimum_is_flagged_skipped() -> None:
    # Opening balance 550,000; after five transfers 300,000; March costs 150,000 extra.
    txns = steady_year([Txn(date(2026, 3, 15), -150_000)])
    result = backtest(txns, current_balance=400_000, monthly_amount=50_000, today=TODAY)
    march, april = result.months[5], result.months[6]
    assert march.month == date(2026, 3, 1)
    assert not march.skipped
    assert march.balance_after == 100_000  # leaving exactly the minimum is allowed
    assert april.skipped
    assert april.transfer == 0
    assert april.balance_after == 100_000
    assert result.skipped_months == tuple(add_months(date(2026, 4, 1), i) for i in range(6))
    assert result.total_saved == 300_000


def test_ac4_short_history_replays_available_months() -> None:
    result = backtest(steady_year(months=4), 1_000_000, 50_000, TODAY)
    assert [m.month for m in result.months] == [add_months(date(2026, 6, 1), i) for i in range(4)]
    assert result.total_saved == 200_000


def test_ac4_current_month_only_shifts_opening_balance() -> None:
    with_october = steady_year([Txn(date(2026, 10, 2), -200_000)])
    assert backtest(with_october, 800_000, 50_000, TODAY) == backtest(
        steady_year(), 1_000_000, 50_000, TODAY
    )


def test_ac4_no_transactions_gives_empty_replay() -> None:
    result = backtest([], 500_000, 50_000, TODAY)
    assert result.months == ()
    assert result.total_saved == 0


def test_backtest_rejects_non_positive_amount() -> None:
    with pytest.raises(ValueError):
        backtest(steady_year(), 1_000_000, 0, TODAY)


transactions = st.lists(
    st.builds(
        Txn,
        booked_on=st.dates(min_value=date(2025, 6, 1), max_value=date(2026, 10, 31)),
        amount=st.integers(min_value=-500_000, max_value=500_000),
    ),
    max_size=60,
)


@given(
    txns=transactions,
    balance=st.integers(min_value=-200_000, max_value=3_000_000),
    amount=st.integers(min_value=1, max_value=300_000),
)
def test_transfer_never_breaks_minimum_balance(txns: list[Txn], balance: Huf, amount: Huf) -> None:
    result = backtest(txns, balance, amount, TODAY)
    assert len(result.months) <= DEFAULTS.backtest_months
    for month in result.months:
        if month.skipped:
            assert month.transfer == 0
            assert month.balance_after == month.balance_before_transfer
            assert month.balance_before_transfer - amount < DEFAULTS.min_balance
        else:
            assert month.transfer == amount
            assert month.balance_after >= DEFAULTS.min_balance
    assert result.total_saved == sum(m.transfer for m in result.months)
    assert result.skipped_months == tuple(m.month for m in result.months if m.skipped)
