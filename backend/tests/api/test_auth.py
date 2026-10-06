import pytest
from django.contrib.auth.models import User
from django.test import Client

pytestmark = pytest.mark.django_db


def login(client: Client, username: str, password: str) -> int:
    response = client.post(
        "/api/auth/login",
        {"username": username, "password": password},
        content_type="application/json",
    )
    return response.status_code


def test_me_requires_login(client: Client) -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_me_returns_customer_role(client: Client) -> None:
    client.force_login(User.objects.create_user(username="anna", password="pw"))
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json() == {"username": "anna", "role": "customer"}


def test_staff_user_has_admin_role(client: Client) -> None:
    client.force_login(User.objects.create_user(username="boss", password="pw", is_staff=True))
    assert client.get("/api/auth/me").json()["role"] == "admin"


def test_login_with_wrong_password_is_rejected(client: Client) -> None:
    User.objects.create_user(username="anna", password="pw")
    assert login(client, "anna", "wrong") == 401


def test_login_then_logout(client: Client) -> None:
    User.objects.create_user(username="anna", password="pw")
    assert login(client, "anna", "pw") == 200
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_csrf_endpoint_sets_token(client: Client) -> None:
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200
    assert response.json()["csrftoken"]
