"""DB test helpers. Uses the same catalogue as `make seed`."""

from collections.abc import Sequence

from django.contrib.auth.models import User

from banking.management.commands.seed import PRODUCTS
from banking.models import Account, Product, Transaction
from banking.synthetic import monthly_series
from rules.money import Huf
from tests.constants import LAST_MONTH


def create_catalogue() -> list[Product]:
    return [
        Product.objects.create(
            code=code, name=name, risk_level=risk, min_horizon_months=horizon, liquid=liquid
        )
        for code, name, risk, horizon, liquid in PRODUCTS
    ]


def create_customer(username: str, surpluses: Sequence[Huf], *, balance: Huf = 1_000_000) -> User:
    user = User.objects.create_user(username=username, password="pw")
    account = Account.objects.create(customer=user, balance=balance)
    Transaction.objects.bulk_create(
        [
            Transaction(
                account=account,
                booked_on=t.booked_on,
                amount=t.amount,
                description=t.description,
                own_transfer=t.own_transfer,
            )
            for t in monthly_series(LAST_MONTH, surpluses)
        ]
    )
    return user
