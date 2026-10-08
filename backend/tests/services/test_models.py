from dataclasses import fields

import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction

from banking.models import Account, Product, Transaction
from plans.models import RuleConfig
from rules.defaults import DEFAULTS
from tests.constants import TODAY

pytestmark = pytest.mark.django_db


def test_rule_config_defaults_match_rules_defaults() -> None:
    assert RuleConfig.load() == DEFAULTS
    assert {f.name for f in fields(DEFAULTS)} <= {f.name for f in RuleConfig._meta.fields}


def test_rule_config_is_a_singleton_and_changes_are_used() -> None:
    config = RuleConfig.objects.create(monthly_share_percent=60)
    config.save()
    RuleConfig(monthly_share_percent=60).save()
    assert RuleConfig.objects.count() == 1
    assert RuleConfig.load().monthly_share_percent == 60


def test_product_risk_level_above_5_is_rejected() -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Product.objects.create(code="x", name="X", risk_level=6)


def test_models_convert_to_rule_types() -> None:
    user = User.objects.create_user(username="anna", password="pw")
    account = Account.objects.create(customer=user, balance=500_000)
    txn = Transaction.objects.create(
        account=account, booked_on=TODAY, amount=-1_000, description="Coffee", own_transfer=False
    )
    product = Product.objects.create(
        code="mm", name="Money market fund", risk_level=1, min_horizon_months=0, liquid=True
    )
    assert txn.to_rule().amount == -1_000
    assert product.to_rule().liquid
    assert product.to_rule().id == product.pk
