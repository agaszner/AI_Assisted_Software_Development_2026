import pytest

from banking.synthetic import monthly_series
from rules.confidence import Confidence, assess_confidence, needs_per_transfer_approval
from rules.surplus import analyse_surplus
from tests.constants import LAST_MONTH, TODAY


def test_ac6_two_months_gives_no_estimate() -> None:
    analysis = analyse_surplus(monthly_series(LAST_MONTH, [60_000, 70_000]), TODAY)
    assert analysis.monthly_amount is None
    assert assess_confidence(analysis.months_of_data) is Confidence.NONE


def test_ac6_four_months_is_low_confidence() -> None:
    analysis = analyse_surplus(monthly_series(LAST_MONTH, [50_000, 60_000, 55_000, 65_000]), TODAY)
    confidence = assess_confidence(analysis.months_of_data)
    assert analysis.monthly_amount == 40_250
    assert confidence is Confidence.LOW
    assert needs_per_transfer_approval(confidence)


@pytest.mark.parametrize(
    ("months", "expected"),
    [
        (0, Confidence.NONE),
        (2, Confidence.NONE),
        (3, Confidence.LOW),
        (5, Confidence.LOW),
        (6, Confidence.NORMAL),
        (12, Confidence.NORMAL),
    ],
)
def test_confidence_boundaries(months: int, expected: Confidence) -> None:
    assert assess_confidence(months) is expected


def test_only_normal_confidence_skips_per_transfer_approval() -> None:
    assert not needs_per_transfer_approval(Confidence.NORMAL)
    assert needs_per_transfer_approval(Confidence.NONE)
