"""AC1 defect check, run against the faulty and the fixed surplus implementation.

Not collected by `make test` (file name does not match test_*.py); run explicitly:
    uv run pytest tests/defects/check_ac1_mean_vs_median.py
Expected: [faulty] FAILS, [fixed] passes.
"""

from collections.abc import Callable

import pytest

import rules.surplus as fixed
from banking.synthetic import monthly_series
from rules.surplus import SurplusAnalysis
from tests.constants import AC1_SERIES, LAST_MONTH, TODAY
from tests.defects import faulty_surplus as faulty


@pytest.mark.parametrize(
    "analyse", [faulty.analyse_surplus, fixed.analyse_surplus], ids=["faulty", "fixed"]
)
def test_ac1_median_surplus_gives_73500(analyse: Callable[..., SurplusAnalysis]) -> None:
    result = analyse(monthly_series(LAST_MONTH, AC1_SERIES), TODAY)
    assert result.median_surplus == 105_000
    assert result.monthly_amount == 73_500
