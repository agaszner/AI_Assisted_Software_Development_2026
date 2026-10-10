from datetime import timedelta
from typing import Any

import pytest
from django.contrib.auth.models import User
from django.test import Client

from banking.models import Product
from core.clock import FixedClock
from plans.execution import run_monthly_orders
from plans.models import Plan, QuestionnaireAnswer, RecurringOrder
from rules.money import Huf
from tests.constants import AC1_SERIES, TODAY
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db

QUESTIONNAIRE: dict[str, Any] = {
    "risk_score": 3,
    "existing_emergency_fund": 750_000,
    "planned_expenses": [],
}


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def post(client: Client, url: str, body: dict[str, Any] | None = None) -> Any:
    return client.post(url, body or {}, content_type="application/json")


def patch(client: Client, url: str, body: dict[str, Any]) -> Any:
    return client.patch(url, body, content_type="application/json")


def login_as(client: Client, username: str, surpluses: list[Huf]) -> User:
    user = create_customer(username, surpluses)
    client.force_login(user)
    return user


def propose(client: Client, questionnaire: dict[str, Any] = QUESTIONNAIRE) -> dict[str, Any]:
    assert post(client, "/api/questionnaire", questionnaire).status_code == 201
    response = post(client, "/api/plans")
    assert response.status_code == 200
    result: dict[str, Any] = response.json()
    return result


def test_main_flow_questionnaire_to_accepted_plan(client: Client) -> None:
    login_as(client, "anna", AC1_SERIES)
    proposal = propose(client)
    analysis = client.get("/api/analysis").json()
    assert (analysis["monthly_amount"], analysis["confidence"]) == (73_500, "normal")
    assert proposal["outcome"] == "plan"
    assert "73,500 HUF" in proposal["explanations"][0]
    plan_id = proposal["plan"]["id"]

    machine = client.get(f"/api/plans/{plan_id}/time-machine").json()
    assert len(machine["months"]) == 6
    assert machine["total_saved"] == 6 * 73_500

    assert post(client, f"/api/plans/{plan_id}/accept").json()["status"] == "accepted"
    assert post(client, f"/api/plans/{plan_id}/accept").status_code == 200
    assert RecurringOrder.objects.count() == 1
    assert client.get("/api/plans/active").json()["id"] == plan_id
    assert post(client, f"/api/plans/{plan_id}/pause").json()["status"] == "paused"


def test_endpoints_require_login(client: Client) -> None:
    assert client.get("/api/analysis").status_code == 401
    assert post(client, "/api/plans").status_code == 401
    assert client.get("/api/plans/1").status_code == 401


def test_no_active_plan_is_404(client: Client) -> None:
    login_as(client, "anna", AC1_SERIES)
    assert client.get("/api/plans/active").status_code == 404


def test_ac5_no_surplus_creates_no_plan(client: Client) -> None:
    login_as(client, "bence", [-40_000] * 6)
    proposal = propose(client)
    assert proposal["outcome"] == "no_surplus"
    assert proposal["plan"] is None
    assert "no surplus" in proposal["explanations"][0]
    assert Plan.objects.count() == 0


def test_ac6_too_little_data_asks_for_expected_savings(client: Client) -> None:
    login_as(client, "csilla", [60_000, 70_000])
    first = propose(client)
    assert first["outcome"] == "needs_expected_savings"
    assert first["plan"] is None
    assert "expect to save" in first["explanations"][0]

    second = propose(client, {**QUESTIONNAIRE, "expected_monthly_savings": 40_000})
    assert second["outcome"] == "plan"
    assert second["plan"]["monthly_amount"] == 40_000
    assert second["plan"]["per_transfer_approval"] is True


def test_ac6_low_confidence_transfer_is_approved_through_api(
    client: Client, clock: FixedClock
) -> None:
    login_as(client, "dani", [50_000, 60_000, 55_000, 65_000])
    plan = propose(client)["plan"]
    assert (plan["confidence"], plan["per_transfer_approval"]) == ("low", True)
    post(client, f"/api/plans/{plan['id']}/accept")
    run_monthly_orders(clock)
    [pending] = client.get("/api/executions").json()
    assert (pending["status"], pending["clause"]) == ("awaiting_approval", 3)
    approved = post(client, f"/api/executions/{pending['id']}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "executed"
    assert post(client, f"/api/executions/{pending['id']}/approve").status_code == 409


@pytest.mark.parametrize(
    "change",
    [
        {"existing_emergency_fund": -1},
        {"expected_monthly_savings": -5},
        {"planned_expenses": [{"name": "Car", "amount": -500_000, "due_on": "2027-08-15"}]},
    ],
)
def test_ac8_negative_amount_is_rejected(client: Client, change: dict[str, Any]) -> None:
    login_as(client, "anna", AC1_SERIES)
    assert post(client, "/api/questionnaire", {**QUESTIONNAIRE, **change}).status_code == 422
    assert QuestionnaireAnswer.objects.count() == 0


@pytest.mark.parametrize("value", [100.0, 100.5, "100", True])
def test_ac8_non_integer_amount_is_rejected(client: Client, value: object) -> None:
    login_as(client, "anna", AC1_SERIES)
    body = {**QUESTIONNAIRE, "existing_emergency_fund": value}
    assert post(client, "/api/questionnaire", body).status_code == 422


def test_out_of_range_risk_score_is_rejected(client: Client) -> None:
    login_as(client, "anna", AC1_SERIES)
    assert post(client, "/api/questionnaire", {**QUESTIONNAIRE, "risk_score": 6}).status_code == 422


def test_ac8_past_expense_date_is_rejected(client: Client) -> None:
    login_as(client, "anna", AC1_SERIES)
    expense = {"name": "Car", "amount": 500_000, "due_on": (TODAY - timedelta(days=1)).isoformat()}
    response = post(client, "/api/questionnaire", {**QUESTIONNAIRE, "planned_expenses": [expense]})
    assert response.status_code == 422
    assert "past" in response.json()["detail"]
    expense["due_on"] = TODAY.isoformat()
    body = {**QUESTIONNAIRE, "planned_expenses": [expense]}
    assert post(client, "/api/questionnaire", body).status_code == 201


def test_ac8_negative_edit_amount_is_rejected(client: Client) -> None:
    login_as(client, "anna", AC1_SERIES)
    plan_id = propose(client)["plan"]["id"]
    assert patch(client, f"/api/plans/{plan_id}", {"monthly_amount": -5}).status_code == 422
    assert patch(client, f"/api/plans/{plan_id}", {"monthly_amount": 80_000}).status_code == 422
    edited = patch(client, f"/api/plans/{plan_id}", {"monthly_amount": 50_000})
    assert edited.status_code == 200
    assert (edited.json()["monthly_amount"], edited.json()["status"]) == (50_000, "proposed")


def test_ac8_other_customer_cannot_view_or_accept_plan(client: Client) -> None:
    login_as(client, "anna", AC1_SERIES)
    plan_id = propose(client)["plan"]["id"]
    client.logout()
    login_as(client, "bob", AC1_SERIES)
    assert client.get(f"/api/plans/{plan_id}").status_code == 403
    assert post(client, f"/api/plans/{plan_id}/accept").status_code == 403
    assert client.get(f"/api/plans/{plan_id}/time-machine").status_code == 403
    assert patch(client, f"/api/plans/{plan_id}", {"monthly_amount": 1_000}).status_code == 403
    assert client.get(f"/api/plans/{plan_id + 999}").status_code == 404
    assert RecurringOrder.objects.count() == 0


def test_accepting_a_rejected_plan_is_a_conflict(client: Client) -> None:
    login_as(client, "anna", AC1_SERIES)
    plan_id = propose(client)["plan"]["id"]
    assert post(client, f"/api/plans/{plan_id}/reject").json()["status"] == "rejected"
    assert post(client, f"/api/plans/{plan_id}/accept").status_code == 409
    assert RecurringOrder.objects.count() == 0


def test_mutating_endpoint_checks_csrf() -> None:
    """Session-authenticated POSTs need the CSRF token (deferred from backend plan Task 1)."""
    strict = Client(enforce_csrf_checks=True)
    login_as(strict, "anna", AC1_SERIES)
    assert post(strict, "/api/questionnaire", QUESTIONNAIRE).status_code == 403
    token = strict.get("/api/auth/csrf").json()["csrftoken"]
    response = strict.post(
        "/api/questionnaire", QUESTIONNAIRE, content_type="application/json", HTTP_X_CSRFTOKEN=token
    )
    assert response.status_code == 201
