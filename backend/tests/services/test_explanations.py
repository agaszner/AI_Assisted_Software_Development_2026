from datetime import date

from plans import explanations
from rules.confidence import Confidence


def test_ac5_no_surplus_message_states_the_median() -> None:
    text = explanations.no_surplus(6, -40_000)
    assert "-40,000 HUF" in text
    assert "no surplus" in text


def test_ac6_message_asks_for_expected_savings() -> None:
    text = explanations.needs_expected_savings(2, 3)
    assert "only 2" in text
    assert "expect to save" in text


def test_plan_summary_uses_rule_results() -> None:
    lines = explanations.plan_summary(
        amount=73_500,
        median_surplus=105_000,
        percent=70,
        months_of_data=6,
        confidence=Confidence.NORMAL,
    )
    assert lines == [
        "We suggest saving 73,500 HUF a month: 70% of your median monthly surplus of 105,000 HUF."
    ]


def test_low_confidence_plan_mentions_approval() -> None:
    lines = explanations.plan_summary(
        amount=40_250,
        median_surplus=57_500,
        percent=70,
        months_of_data=4,
        confidence=Confidence.LOW,
    )
    assert len(lines) == 2
    assert "approval" in lines[1]


def test_skipped_month_message() -> None:
    text = explanations.skipped_month(date(2026, 4, 1), 100_000)
    assert text.startswith("2026-04")
    assert "100,000 HUF" in text
