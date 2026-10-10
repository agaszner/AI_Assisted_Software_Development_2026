"""Questionnaire answers, plans, mandates, recurring orders, executions and the audit log."""

from dataclasses import fields
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from banking.models import Product
from rules.confidence import Confidence, needs_per_transfer_approval
from rules.defaults import DEFAULTS, RuleParams
from rules.mandate import MandateTerms

USER = settings.AUTH_USER_MODEL


def _months(default: int) -> Any:  # field classes are not subscriptable at runtime
    return models.PositiveSmallIntegerField(default=default, validators=[MinValueValidator(1)])


class RuleConfig(models.Model):
    """Rule parameters (AGENTS.md section 6). Singleton (pk=1), edited in Django admin."""

    monthly_share_percent = models.PositiveSmallIntegerField(
        default=DEFAULTS.monthly_share_percent,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    surplus_window_months = _months(DEFAULTS.surplus_window_months)
    min_months_for_estimate = _months(DEFAULTS.min_months_for_estimate)
    full_confidence_months = _months(DEFAULTS.full_confidence_months)
    emergency_fund_months = _months(DEFAULTS.emergency_fund_months)
    liquid_horizon_months = _months(DEFAULTS.liquid_horizon_months)
    low_risk_max = models.PositiveSmallIntegerField(
        default=DEFAULTS.low_risk_max, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    min_balance = models.BigIntegerField(
        default=DEFAULTS.min_balance, validators=[MinValueValidator(0)]
    )
    backtest_months = _months(DEFAULTS.backtest_months)

    class Meta:
        verbose_name = "rule configuration"

    def __str__(self) -> str:
        return "Rule configuration"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> RuleParams:
        config, _ = cls.objects.get_or_create(pk=1)
        return RuleParams(**{f.name: getattr(config, f.name) for f in fields(RuleParams)})


class QuestionnaireAnswer(models.Model):
    customer = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="questionnaires")
    risk_score = models.PositiveSmallIntegerField()
    existing_emergency_fund = models.BigIntegerField()
    expected_monthly_savings = models.BigIntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField()


class ExpenseAnswer(models.Model):
    questionnaire = models.ForeignKey(
        QuestionnaireAnswer, on_delete=models.CASCADE, related_name="expenses"
    )
    name = models.CharField(max_length=100)
    amount = models.BigIntegerField()
    due_on = models.DateField()


class Plan(models.Model):
    class Status(models.TextChoices):
        PROPOSED = "proposed"
        ACCEPTED = "accepted"
        REJECTED = "rejected"
        PAUSED = "paused"

    customer = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="plans")
    questionnaire = models.ForeignKey(QuestionnaireAnswer, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PROPOSED)
    monthly_amount = models.BigIntegerField()
    proposed_amount = models.BigIntegerField(
        help_text="Rule-engine amount; edits may only lower it."
    )
    median_surplus = models.BigIntegerField(null=True, blank=True)
    median_expenses = models.BigIntegerField()
    months_of_data = models.PositiveSmallIntegerField()
    confidence = models.CharField(max_length=10, choices=[(c.value, c.value) for c in Confidence])
    created_at = models.DateTimeField()

    @property
    def per_transfer_approval(self) -> bool:
        return needs_per_transfer_approval(Confidence(self.confidence))


class PlanItem(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="items")
    position = models.PositiveSmallIntegerField()
    kind = models.CharField(max_length=20)
    label = models.CharField(max_length=100)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    monthly_amount = models.BigIntegerField()
    target_amount = models.BigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["plan", "position"], name="plan_item_position_unique")
        ]


class Mandate(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active"
        PAUSED = "paused"

    customer = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="mandates")
    plan = models.OneToOneField(Plan, on_delete=models.PROTECT, related_name="mandate")
    version = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    max_monthly_amount = models.BigIntegerField()
    min_balance = models.BigIntegerField()
    per_transfer_approval = models.BooleanField()
    products = models.ManyToManyField(Product)
    signed_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["customer", "version"], name="mandate_version_unique")
        ]

    def terms(self) -> MandateTerms:
        return MandateTerms(
            version=self.version,
            active=self.status == self.Status.ACTIVE,
            max_monthly_amount=self.max_monthly_amount,
            min_balance=self.min_balance,
            allowed_product_ids=frozenset(self.products.values_list("id", flat=True)),
            per_transfer_approval=self.per_transfer_approval,
        )


class RecurringOrder(models.Model):
    """One per plan item. The OneToOne field makes "exactly once" a DB guarantee (AC7)."""

    class Status(models.TextChoices):
        ACTIVE = "active"
        PAUSED = "paused"

    plan_item = models.OneToOneField(PlanItem, on_delete=models.PROTECT, related_name="order")
    mandate = models.ForeignKey(Mandate, on_delete=models.PROTECT, related_name="orders")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    monthly_amount = models.BigIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)


class Execution(models.Model):
    """One monthly run of one order. The unique idempotency key prevents duplicates (AC7)."""

    class Status(models.TextChoices):
        EXECUTED = "executed"
        DENIED = "denied"
        AWAITING_APPROVAL = "awaiting_approval"

    order = models.ForeignKey(RecurringOrder, on_delete=models.PROTECT, related_name="executions")
    period = models.DateField(help_text="First day of the month this execution belongs to.")
    idempotency_key = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    amount = models.BigIntegerField()
    mandate_version = models.PositiveIntegerField()
    clause = models.PositiveSmallIntegerField()
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField()


class LogEntry(models.Model):
    customer = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="log_entries")
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    event = models.CharField(max_length=50)
    message = models.TextField()
    mandate_version = models.PositiveIntegerField(null=True, blank=True)
    clause = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        ordering = ["created_at", "id"]
