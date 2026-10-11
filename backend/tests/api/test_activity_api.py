from typing import Any

import pytest
from django.test import Client

from banking.models import Product
from core.clock import FixedClock
from plans.execution import run_monthly_orders
from plans.models import RecurringOrder
from tests.constants import AC1_SERIES
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db

ANSWERS: dict[str, Any] = {"risk_score": 3, "existing_emergency_fund": 0, "planned_expenses": []}
SIGN = {"password": "pw"}


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def post(client: Client, url: str, body: dict[str, Any] | None = None) -> Any:
    return client.post(url, body or {}, content_type="application/json")


def accepted(client: Client, username: str, surpluses: list[int]) -> dict[str, Any]:
    client.force_login(create_customer(username, surpluses))
    post(client, "/api/questionnaire", ANSWERS)
    plan: dict[str, Any] = post(client, "/api/plans").json()["plan"]
    assert post(client, f"/api/plans/{plan['id']}/accept", SIGN).status_code == 200
    return plan


def test_activity_shows_scheduled_transfers_then_events(client: Client) -> None:
    plan = accepted(client, "anna", AC1_SERIES)
    rows = client.get("/api/activity").json()
    scheduled = [r for r in rows if r["status"] == "scheduled"]
    orders = RecurringOrder.objects.filter(plan_item__plan_id=plan["id"]).order_by("id")
    assert [r["idempotency_key"] for r in scheduled] == [f"order-{o.pk}-2026-11" for o in orders]
    assert {r["on"] for r in scheduled} == {"2026-11-01"}
    assert {r["clause"] for r in scheduled} == {"Will be checked against §1 and §2"}
    assert {r["logged_at"] for r in scheduled} == {None}
    events = rows[len(scheduled) :]
    assert [(r["title"], r["status"]) for r in events] == [
        (
            f"You accepted the plan and signed mandate version 1: {len(plan['items'])} monthly "
            "transfers set up",
            "done",
        ),
        ("Plan proposed: 73,500 HUF a month", "proposed"),
    ]
    assert events[0]["amount"] == 73_500 and events[0]["mandate_version"] == 1


def test_ac6_waiting_transfer_offers_approval(client: Client, clock: FixedClock) -> None:
    accepted(client, "dani", [50_000, 60_000, 55_000, 65_000])
    run_monthly_orders(clock)
    [waiting] = [
        r for r in client.get("/api/activity").json() if r["status"] == "awaiting_approval"
    ]
    assert waiting["execution_id"] is not None
    assert waiting["clause"] == "§3 · This transfer needs your approval."
    assert waiting["on"] == "2026-10-01" and waiting["logged_at"] is not None
    assert post(client, f"/api/executions/{waiting['execution_id']}/approve").status_code == 200
    statuses = {r["key"]: r["status"] for r in client.get("/api/activity").json()}
    assert statuses[waiting["key"]] == "executed"


def test_activity_is_private(client: Client) -> None:
    accepted(client, "anna", AC1_SERIES)
    client.logout()
    client.force_login(create_customer("bob", AC1_SERIES))
    assert client.get("/api/activity").json() == []
