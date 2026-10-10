from datetime import date

import pytest

from banking.synthetic import monthly_series
from rules.surplus import MonthFlow, analyse_surplus
from rules.types import Txn
from tests.constants import AC1_SERIES, LAST_MONTH, TODAY


def test_ac1_median_surplus_gives_73500() -> None:
    result = analyse_surplus(monthly_series(LAST_MONTH, AC1_SERIES), TODAY)
    assert [flow.surplus for flow in result.flows] == AC1_SERIES
    assert result.median_surplus == 105_000
    assert result.monthly_amount == 73_500


def test_ac1_own_account_transfers_are_ignored() -> None:
    txns = monthly_series(LAST_MONTH, AC1_SERIES)
    txns.append(Txn(date(2026, 9, 15), -500_000, own_transfer=True))
    assert analyse_surplus(txns, TODAY).monthly_amount == 73_500


def test_ac1_current_partial_month_is_ignored() -> None:
    txns = monthly_series(LAST_MONTH, AC1_SERIES)
    txns.append(Txn(date(2026, 10, 2), 1_000_000))
    result = analyse_surplus(txns, TODAY)
    assert result.monthly_amount == 73_500
    assert result.flows[-1].month == LAST_MONTH


def test_ac1_only_last_six_months_count() -> None:
    txns = monthly_series(LAST_MONTH, [5_000_000, 5_000_000, *AC1_SERIES])
    result = analyse_surplus(txns, TODAY)
    assert result.months_of_data == 8
    assert result.monthly_amount == 73_500


def test_month_without_transactions_counts_as_zero_surplus() -> None:
    # March–May and July–September have data, June has none.
    txns = monthly_series(date(2026, 5, 1), [100_000] * 3) + monthly_series(
        LAST_MONTH, [100_000] * 3
    )
    result = analyse_surplus(txns, TODAY)
    assert result.months_of_data == 7
    assert result.flows[2] == MonthFlow(date(2026, 6, 1), income=0, expenses=0)
    assert result.median_surplus == 100_000


def test_even_median_rounds_down() -> None:
    result = analyse_surplus(monthly_series(LAST_MONTH, [10_001, 10_002, 10_003, 10_004]), TODAY)
    assert result.median_surplus == 10_002
    assert result.monthly_amount == 7_001


def test_ac5_negative_median_gives_no_amount() -> None:
    result = analyse_surplus(monthly_series(LAST_MONTH, [-50_000] * 6), TODAY)
    assert result.median_surplus == -50_000
    assert result.monthly_amount == 0


def test_ac5_zero_median_gives_no_amount() -> None:
    # ADR-0002: a median of exactly 0 also means no surplus.
    result = analyse_surplus(monthly_series(LAST_MONTH, [0] * 6), TODAY)
    assert result.monthly_amount == 0


def test_too_little_data_gives_no_estimate_but_keeps_expenses() -> None:
    result = analyse_surplus(monthly_series(LAST_MONTH, [60_000, 70_000]), TODAY)
    assert result.months_of_data == 2
    assert result.median_surplus is None
    assert result.monthly_amount is None
    assert result.median_expenses == 250_000


def test_no_transactions_at_all() -> None:
    result = analyse_surplus([], TODAY)
    assert result.months_of_data == 0
    assert result.flows == ()
    assert result.median_expenses == 0
    assert result.monthly_amount is None


def test_synthetic_series_rejects_impossible_surplus() -> None:
    with pytest.raises(ValueError):
        monthly_series(LAST_MONTH, [-300_000])
