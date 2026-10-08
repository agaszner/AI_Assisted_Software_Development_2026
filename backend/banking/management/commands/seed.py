"""Load the product catalogue, the admin user and synthetic personas. Safe to re-run:
existing users are left unchanged. Dates are relative to the injected clock."""

import os
from typing import Any

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from banking.models import Account, Product, Transaction
from banking.synthetic import monthly_series
from core.clock import get_clock
from rules.months import add_months, month_of

# code, name, risk level, minimum horizon (months), liquid
PRODUCTS: list[tuple[str, str, int, int, bool]] = [
    ("money-market", "Money market fund", 1, 0, True),
    ("short-bond", "Short government bond fund", 2, 0, True),
    ("gov-bond-3y", "3-year government bond", 2, 24, False),
    ("balanced", "Balanced fund", 3, 36, False),
    ("equity", "Global equity fund", 5, 60, False),
]

# username, monthly surpluses (oldest first, ending last month), opening balance
PERSONAS: list[tuple[str, list[int], int]] = [
    ("anna", [100_000, 120_000, 80_000, 110_000, 90_000, 300_000], 600_000),  # AC1, AC2
    ("bence", [-40_000] * 6, 300_000),  # AC5: no surplus
    ("csilla", [60_000, 70_000], 400_000),  # AC6: 2 months → no estimate
    ("dani", [50_000, 60_000, 55_000, 65_000], 400_000),  # AC6: 4 months → low confidence
]


class Command(BaseCommand):
    help = "Load synthetic personas, the product catalogue and the admin user."

    def handle(self, *args: Any, **options: Any) -> None:
        password = os.environ.get("SEED_PASSWORD")
        if not password:
            raise CommandError("Set SEED_PASSWORD in .env (see .env.example).")
        last_month = add_months(month_of(get_clock().today()), -1)
        with transaction.atomic():
            for code, name, risk, horizon, liquid in PRODUCTS:
                Product.objects.update_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "risk_level": risk,
                        "min_horizon_months": horizon,
                        "liquid": liquid,
                    },
                )
            if not User.objects.filter(username="admin").exists():
                User.objects.create_superuser(username="admin", password=password)
            for username, surpluses, opening in PERSONAS:
                if User.objects.filter(username=username).exists():
                    continue
                user = User.objects.create_user(username=username, password=password)
                txns = monthly_series(last_month, surpluses)
                account = Account.objects.create(
                    customer=user, balance=opening + sum(t.amount for t in txns)
                )
                Transaction.objects.bulk_create(
                    [
                        Transaction(
                            account=account,
                            booked_on=t.booked_on,
                            amount=t.amount,
                            description=t.description,
                            own_transfer=t.own_transfer,
                        )
                        for t in txns
                    ]
                )
        self.stdout.write(
            self.style.SUCCESS(f"Seeded {len(PRODUCTS)} products and {len(PERSONAS)} personas.")
        )
