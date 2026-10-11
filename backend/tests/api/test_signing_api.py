from typing import Any

import pytest
from django.test import Client

from banking.models import Product
from plans.models import Mandate, RecurringOrder
from tests.constants import AC1_SERIES
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db

ANSWERS: dict[str, Any] = {
    "risk_score": 3,
    "existing_emergency_fund": 750_000,
    "planned_expenses": [],
}
SIGN = {"password": "pw"}  # tests.factories.create_customer's password


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def post(client: Client, url: str, body: dict[str, Any] | None = None) -> Any:
    return client.post(url, body or {}, content_type="application/json")


def proposed_id(client: Client, username: str = "anna") -> int:
    client.force_login(create_customer(username, AC1_SERIES))
    assert post(client, "/api/questionnaire", ANSWERS).status_code == 201
    plan_id: int = post(client, "/api/plans").json()["plan"]["id"]
    return plan_id


def test_ac7_wrong_password_signs_nothing(client: Client) -> None:
    plan_id = proposed_id(client)
    response = post(client, f"/api/plans/{plan_id}/accept", {"password": "wrong"})
    assert (response.status_code, response.json()) == (403, {"detail": "Incorrect password."})
    assert not Mandate.objects.exists() and not RecurringOrder.objects.exists()
    assert client.get(f"/api/plans/{plan_id}").json()["status"] == "proposed"
    assert post(client, f"/api/plans/{plan_id}/accept", SIGN).json()["status"] == "accepted"
    assert post(client, f"/api/plans/{plan_id}/accept", SIGN).status_code == 200
    assert RecurringOrder.objects.count() == len(
        client.get(f"/api/plans/{plan_id}").json()["items"]
    )


def test_accept_without_password_is_rejected(client: Client) -> None:
    plan_id = proposed_id(client)
    assert post(client, f"/api/plans/{plan_id}/accept").status_code == 422


def test_ac8_own_password_cannot_sign_another_customers_plan(client: Client) -> None:
    plan_id = proposed_id(client)
    client.logout()
    client.force_login(create_customer("bob", AC1_SERIES))
    response = post(client, f"/api/plans/{plan_id}/accept", SIGN)
    assert response.status_code == 403
    assert response.json()["detail"] == "This plan belongs to another customer."


def test_revise_endpoint_returns_the_revision_and_signing_gives_version_2(client: Client) -> None:
    plan_id = proposed_id(client)
    post(client, f"/api/plans/{plan_id}/accept", SIGN)
    revision = post(client, f"/api/plans/{plan_id}/revise", {"monthly_amount": 50_000}).json()
    assert (revision["status"], revision["revises"], revision["monthly_amount"]) == (
        "proposed",
        plan_id,
        50_000,
    )
    assert client.get("/api/plans/active").json()["pending_revision"] == revision["id"]
    assert client.get(f"/api/plans/{revision['id']}/mandate").json()["version"] == 2
    assert post(client, f"/api/plans/{revision['id']}/accept", SIGN).json()["mandate_version"] == 2
    assert client.get("/api/plans/active").json()["id"] == revision["id"]
    assert client.get(f"/api/plans/{plan_id}").json()["status"] == "paused"


def test_revise_errors_name_the_field(client: Client) -> None:
    plan_id = proposed_id(client)
    post(client, f"/api/plans/{plan_id}/accept", SIGN)
    response = post(client, f"/api/plans/{plan_id}/revise", {"monthly_amount": 100_000})
    assert response.status_code == 422
    assert response.json()["field"] == "monthly_amount"


def test_ac8_other_customer_cannot_revise(client: Client) -> None:
    plan_id = proposed_id(client)
    post(client, f"/api/plans/{plan_id}/accept", SIGN)
    client.logout()
    client.force_login(create_customer("bob", AC1_SERIES))
    assert (
        post(client, f"/api/plans/{plan_id}/revise", {"monthly_amount": 50_000}).status_code == 403
    )
