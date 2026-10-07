"""Deterministic synthetic transactions for `make seed` and tests. Pure: no Django, no clock."""

from collections.abc import Sequence
from datetime import date

from rules.money import Huf
from rules.months import add_months
from rules.types import Txn

DEFAULT_EXPENSES: Huf = 250_000
OWN_TRANSFER: Huf = 30_000


def monthly_series(
    last_month: date, surpluses: Sequence[Huf], *, expenses: Huf = DEFAULT_EXPENSES
) -> list[Txn]:
    """One month of transactions per surplus value, oldest first, ending with `last_month`.

    Each month: rent (60 % of expenses), salary (expenses + surplus), bills (the rest of the
    expenses) and an own-account transfer, which the surplus calculation must ignore.
    """
    first = add_months(last_month, -(len(surpluses) - 1))
    rent = expenses * 6 // 10
    txns: list[Txn] = []
    for index, surplus in enumerate(surpluses):
        income = expenses + surplus
        if income < 0:
            raise ValueError(f"surplus {surplus} is below -expenses ({-expenses})")
        month = add_months(first, index)
        txns += [
            Txn(month.replace(day=3), -rent, description="Rent"),
            Txn(month.replace(day=10), income, description="Salary"),
            Txn(month.replace(day=20), -(expenses - rent), description="Groceries and bills"),
            Txn(
                month.replace(day=25),
                -OWN_TRANSFER,
                own_transfer=True,
                description="To own savings account",
            ),
        ]
    return txns
