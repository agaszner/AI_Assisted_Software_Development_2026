import pytest
from django.contrib.auth.models import User
from django.core.management import CommandError, call_command

from banking.models import Account, Product, Transaction
from rules.surplus import analyse_surplus
from tests.constants import TODAY

pytestmark = pytest.mark.django_db


@pytest.fixture
def seed_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEED_PASSWORD", "demo-only")


@pytest.mark.usefixtures("seed_password")
def test_seed_is_safe_to_run_twice() -> None:
    call_command("seed")
    call_command("seed")
    assert User.objects.filter(username="anna").count() == 1
    assert Transaction.objects.filter(account__customer__username="anna").count() == 24
    assert Product.objects.count() == 5
    assert User.objects.get(username="admin").is_staff


@pytest.mark.usefixtures("seed_password")
def test_seeded_anna_gives_the_ac1_amount() -> None:
    call_command("seed")
    txns = [t.to_rule() for t in Transaction.objects.filter(account__customer__username="anna")]
    assert analyse_surplus(txns, TODAY).monthly_amount == 73_500


@pytest.mark.usefixtures("seed_password")
def test_seeded_balance_matches_transactions() -> None:
    call_command("seed")
    account = Account.objects.get(customer__username="anna")
    total = sum(t.amount for t in account.transactions.all())
    assert account.balance == 600_000 + total


def test_seed_without_password_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SEED_PASSWORD", raising=False)
    with pytest.raises(CommandError):
        call_command("seed")
