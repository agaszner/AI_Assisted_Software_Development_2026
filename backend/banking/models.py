"""Simulated bank: current accounts, their transactions and the product catalogue."""

from django.conf import settings
from django.db import models

from rules.types import ProductInfo, Txn


class Account(models.Model):
    """A customer's simulated current account. Balance in whole forints."""

    customer = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="account"
    )
    name = models.CharField(max_length=100, default="Current account")
    balance = models.BigIntegerField()

    def __str__(self) -> str:
        return f"{self.customer} – {self.name}"


class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
    booked_on = models.DateField()
    amount = models.BigIntegerField(help_text="Positive: income, negative: expense (HUF).")
    description = models.CharField(max_length=200, blank=True)
    own_transfer = models.BooleanField(
        default=False,
        help_text="Between the customer's own accounts or a SaverAI transfer; ignored in surplus.",
    )

    class Meta:
        ordering = ["booked_on", "id"]

    def to_rule(self) -> Txn:
        return Txn(
            booked_on=self.booked_on,
            amount=self.amount,
            own_transfer=self.own_transfer,
            description=self.description,
        )


class Product(models.Model):
    """Catalogue entry, managed by the Admin role in Django admin."""

    code = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    risk_level = models.PositiveSmallIntegerField(help_text="1 (lowest) to 5 (highest).")
    min_horizon_months = models.PositiveSmallIntegerField(default=0)
    liquid = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["risk_level", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(risk_level__gte=1, risk_level__lte=5),
                name="product_risk_level_1_to_5",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} (risk {self.risk_level})"

    def to_rule(self) -> ProductInfo:
        return ProductInfo(
            id=self.pk,
            name=self.name,
            risk_level=self.risk_level,
            min_horizon_months=self.min_horizon_months,
            liquid=self.liquid,
        )
