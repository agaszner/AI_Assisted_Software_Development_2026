from datetime import timedelta
from typing import Any

import pytest
from django.contrib.auth.models import User
from django.test import Client

from banking.models import Account, Product, Transaction
from plans.models import RuleConfig
from rules.mandate import CLAUSES
from tests.constants import AC1_SERIES, TODAY
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db

QUESTIONNAIRE: dict[str, Any] = {
    "risk_score": 3,
    "existing_emergency_fund": 750_000,
    "planned_expenses": [],
}
SIGN = {"password": "pw"}  # create_customer's password (ADR-0004)


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def post(client: Client, url: str, body: dict[str, Any] | None = None) -> Any:
    return client.post(url, body or {}, content_type="application/json")


def proposed_plan_id(client: Client) -> int:
    assert post(client, "/api/questionnaire", QUESTIONNAIRE).status_code == 201
    plan_id: int = post(client, "/api/plans").json()["plan"]["id"]
    return plan_id


def test_account_requires_login(client: Client) -> None:
    assert client.get("/api/account").status_code == 401


def test_account_shows_today_balance_minimum_and_five_newest_transactions(client: Client) -> None:
    client.force_login(create_customer("anna", AC1_SERIES, balance=600_000))
    body = client.get("/api/account").json()
    assert (body["today"], body["balance"], body["min_balance"]) == (
        TODAY.isoformat(),
        600_000,
        100_000,
    )
    dates = [t["booked_on"] for t in body["transactions"]]
    assert len(dates) == 5
    assert dates == sorted(dates, reverse=True)
    assert {"own_transfer", "description"} <= set(body["transactions"][0])


def test_account_hides_transactions_after_today(client: Client) -> None:
    user = create_customer("anna", AC1_SERIES)
    Transaction.objects.create(
        account=Account.objects.get(customer=user),
        booked_on=TODAY + timedelta(days=1),
        amount=-1,
        description="Future",
    )
    client.force_login(user)
    descriptions = [t["description"] for t in client.get("/api/account").json()["transactions"]]
    assert "Future" not in descriptions


def test_user_without_account_gets_404(client: Client) -> None:
    client.force_login(User.objects.create_user(username="nobody", password="pw"))
    assert client.get("/api/account").status_code == 404


def test_mandate_preview_matches_signed_mandate(client: Client) -> None:
    client.force_login(create_customer("anna", AC1_SERIES))
    plan_id = proposed_plan_id(client)

    preview = client.get(f"/api/plans/{plan_id}/mandate").json()
    assert (preview["status"], preview["version"], preview["signed_at"]) == ("unsigned", 1, None)
    assert (preview["max_monthly_amount"], preview["min_balance"]) == (73_500, 100_000)
    assert [c["number"] for c in preview["clauses"]] == sorted(CLAUSES)
    assert preview["products"]

    assert post(client, f"/api/plans/{plan_id}/accept", SIGN).status_code == 200
    signed = client.get(f"/api/plans/{plan_id}/mandate").json()
    assert (signed["status"], signed["version"]) == ("active", 1)
    assert signed["signed_at"] is not None
    for key in (
        "version",
        "max_monthly_amount",
        "min_balance",
        "per_transfer_approval",
        "products",
        "clauses",
    ):
        assert signed[key] == preview[key], key


def test_rules_follow_rule_config(client: Client) -> None:
    client.force_login(create_customer("anna", AC1_SERIES))
    lines = client.get("/api/rules").json()["lines"]
    assert lines[0] == "Monthly amount = 70% of your median monthly surplus (last 6 months)."
    assert (
        lines[3] == "A transfer is skipped if it would leave less than 100,000 HUF on your account."
    )
    config = RuleConfig.objects.get_or_create(pk=1)[0]
    config.monthly_share_percent = 60
    config.save()
    assert client.get("/api/rules").json()["lines"][0].startswith("Monthly amount = 60%")


def test_ac8_other_customer_cannot_view_mandate(client: Client) -> None:
    client.force_login(create_customer("anna", AC1_SERIES))
    plan_id = proposed_plan_id(client)
    client.logout()
    client.force_login(create_customer("bob", AC1_SERIES))
    assert client.get(f"/api/plans/{plan_id}/mandate").status_code == 403
