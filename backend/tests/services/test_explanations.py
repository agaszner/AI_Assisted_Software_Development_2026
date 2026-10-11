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


def test_rule_lines_are_filled_from_parameters() -> None:
    from rules.defaults import DEFAULTS

    assert explanations.rule_lines(DEFAULTS) == [
        "Monthly amount = 70% of your median monthly surplus (last 6 months).",
        "Priority: emergency fund (3× median monthly expenses), then planned expenses, then "
        "long-term investment.",
        "Money needed within 12 months goes only to low-risk, liquid products.",
        "A transfer is skipped if it would leave less than 100,000 HUF on your account.",
    ]


def test_median_working_shows_the_sorted_values_and_the_middle() -> None:
    assert explanations.median_working(
        [100_000, 120_000, 80_000, 110_000, 90_000, 300_000], 105_000
    ) == (
        "Sorted: 80,000 · 90,000 · 100,000 · 110,000 · 120,000 · 300,000. "
        "Median = (100,000 + 110,000) / 2 = 105,000 HUF."
    )
    assert explanations.median_working([3, 1, 2], 2) == "Sorted: 1 · 2 · 3. Median = 2 HUF."


def test_activity_titles() -> None:
    assert explanations.transfer_title("emergency_fund", "Emergency fund", 30_000) == (
        "30,000 HUF to your emergency fund"
    )
    assert explanations.transfer_title("planned_expense", "New laptop", 30_000) == (
        "30,000 HUF to your New laptop savings"
    )
    assert explanations.transfer_title("investment", "Long-term investment", 13_500) == (
        "13,500 HUF to long-term investment"
    )
    assert explanations.event_title("plan_accepted", amount=73_500, version=1, orders=3) == (
        "You accepted the plan and signed mandate version 1: 3 monthly transfers set up"
    )
    assert explanations.event_title("plan_proposed", amount=73_500, version=None, orders=0) == (
        "Plan proposed: 73,500 HUF a month"
    )
    assert explanations.event_title("execution_executed", amount=1, version=1, orders=0) is None
    assert explanations.scheduled_check(False) == "Will be checked against §1 and §2"
    assert explanations.scheduled_check(True) == "Will be checked against §1, §2 and §3"
    assert explanations.decision_text(3, "This transfer needs your approval.") == (
        "§3 · This transfer needs your approval."
    )
