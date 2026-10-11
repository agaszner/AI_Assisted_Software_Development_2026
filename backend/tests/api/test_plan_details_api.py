from typing import Any

import pytest
from django.test import Client

from banking.models import Product
from core.clock import FixedClock
from plans.execution import run_monthly_orders
from tests.constants import AC1_SERIES, TODAY
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db

ANSWERS: dict[str, Any] = {
    "risk_score": 2,
    "existing_emergency_fund": 720_000,
    "planned_expenses": [{"name": "New laptop", "amount": 300_000, "due_on": "2027-08-01"}],
}
SIGN = {"password": "pw"}  # create_customer's password (ADR-0004)


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def post(client: Client, url: str, body: dict[str, Any] | None = None) -> Any:
    return client.post(url, body or {}, content_type="application/json")


def proposed(client: Client, answers: dict[str, Any] = ANSWERS) -> dict[str, Any]:
    client.force_login(create_customer("anna", AC1_SERIES))
    assert post(client, "/api/questionnaire", answers).status_code == 201
    plan: dict[str, Any] = post(client, "/api/plans").json()["plan"]
    return plan


def test_plan_shows_the_values_of_the_review_screen(client: Client) -> None:
    plan = proposed(client)
    assert plan["created_on"] == TODAY.isoformat()
    assert (plan["median_surplus"], plan["months_of_data"], plan["share_percent"]) == (
        105_000,
        6,
        70,
    )
    assert (plan["risk_score"], plan["min_balance"]) == (2, 100_000)
    assert plan["next_transfer_on"] == "2026-11-01"
    assert (plan["mandate_version"], plan["signed_on"], plan["saved_total"]) == (None, None, 0)


def test_items_show_position_due_date_and_progress(client: Client) -> None:
    items = proposed(client)["items"]
    assert [i["position"] for i in items] == list(range(len(items)))
    fund, laptop = items[0], items[1]
    assert fund["kind"] == "emergency_fund"
    assert fund["saved_amount"] == 720_000  # the fund the customer already has
    assert fund["progress_percent"] == min(100, 720_000 * 100 // fund["target_amount"])
    assert (laptop["label"], laptop["due_on"]) == ("New laptop", "2027-08-01")
    assert (laptop["saved_amount"], laptop["progress_percent"]) == (0, 0)


def test_executed_transfers_count_as_saved(client: Client, clock: FixedClock) -> None:
    plan = proposed(client)
    assert post(client, f"/api/plans/{plan['id']}/accept", SIGN).status_code == 200
    run_monthly_orders(clock)
    after = client.get(f"/api/plans/{plan['id']}").json()
    assert (after["mandate_version"], after["signed_on"]) == (1, TODAY.isoformat())
    assert after["saved_total"] == plan["monthly_amount"]
    fund = after["items"][0]
    assert fund["saved_amount"] == 720_000 + fund["monthly_amount"]


def test_analysis_explains_the_median(client: Client) -> None:
    proposed(client)
    body = client.get("/api/analysis").json()
    assert body["share_percent"] == 70
    assert body["median_explanation"].endswith("Median = (100,000 + 110,000) / 2 = 105,000 HUF.")
    assert body["explanations"] == []


def test_ac5_analysis_explains_no_surplus(client: Client) -> None:
    client.force_login(create_customer("bence", [-40_000] * 6))
    body = client.get("/api/analysis").json()
    assert body["explanations"] and "no surplus" in body["explanations"][0]


def test_ac6_analysis_asks_for_expected_savings(client: Client) -> None:
    client.force_login(create_customer("csilla", [50_000, 60_000]))
    body = client.get("/api/analysis").json()
    assert body["median_explanation"] is None
    assert "expect to save" in body["explanations"][0]


def test_time_machine_counts_transfers(client: Client) -> None:
    plan = proposed(client)
    body = client.get(f"/api/plans/{plan['id']}/time-machine").json()
    assert body["months_replayed"] == len(body["months"])
    assert body["transfers_made"] == sum(1 for m in body["months"] if not m["skipped"])


def test_ac8_past_expense_date_names_the_field(client: Client) -> None:
    client.force_login(create_customer("anna", AC1_SERIES))
    answers = {
        **ANSWERS,
        "planned_expenses": [
            {"name": "New laptop", "amount": 300_000, "due_on": "2027-08-01"},
            {"name": "Holiday", "amount": 50_000, "due_on": "2026-09-01"},
        ],
    }
    response = post(client, "/api/questionnaire", answers)
    assert response.status_code == 422
    assert response.json() == {
        "detail": "The due date of 'Holiday' (2026-09-01) is in the past.",
        "field": "planned_expenses.1.due_on",
    }
