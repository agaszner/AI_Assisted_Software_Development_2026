from datetime import date

import pytest

from rules.defaults import DEFAULTS
from rules.money import ceil_div, median, percent_of
from rules.months import add_months, month_of, months_between


def test_percent_of_rounds_down_to_whole_forint() -> None:
    assert percent_of(105_000, 70) == 73_500
    assert percent_of(10_001, 70) == 7_000  # 7000.7 → 7000


def test_median_odd_and_even_counts() -> None:
    assert median([3, 1, 2]) == 2
    assert median([110_000, 100_000]) == 105_000
    assert median([10_002, 10_003]) == 10_002  # 10002.5 rounds down
    assert median([-1, 0]) == -1  # rounds down, also below zero


def test_median_of_empty_sequence_raises() -> None:
    with pytest.raises(ValueError):
        median([])


def test_ceil_div_rounds_up() -> None:
    assert ceil_div(500_000, 10) == 50_000
    assert ceil_div(100, 3) == 34


def test_month_helpers() -> None:
    assert month_of(date(2026, 10, 6)) == date(2026, 10, 1)
    assert add_months(date(2026, 11, 1), 2) == date(2027, 1, 1)
    assert add_months(date(2026, 1, 1), -1) == date(2025, 12, 1)
    assert months_between(date(2026, 10, 1), date(2027, 8, 1)) == 10


def test_defaults_match_specification() -> None:
    assert DEFAULTS.monthly_share_percent == 70
    assert DEFAULTS.surplus_window_months == 6
    assert DEFAULTS.min_months_for_estimate == 3
    assert DEFAULTS.full_confidence_months == 6
    assert DEFAULTS.emergency_fund_months == 3
    assert DEFAULTS.liquid_horizon_months == 12
    assert DEFAULTS.min_balance == 100_000
    assert DEFAULTS.backtest_months == 12
