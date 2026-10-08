from dataclasses import replace

from hypothesis import given
from hypothesis import strategies as st

from rules.mandate import (
    APPROVAL_CLAUSE,
    AUTHORISING_CLAUSE,
    CLAUSES,
    MIN_BALANCE_CLAUSE,
    PAUSE_CLAUSE,
    MandateTerms,
    TransferAction,
    check_action,
)

MANDATE = MandateTerms(
    version=3,
    active=True,
    max_monthly_amount=73_500,
    min_balance=100_000,
    allowed_product_ids=frozenset({2, 4}),
    per_transfer_approval=False,
)
ACTION = TransferAction(
    product_id=4,
    amount=73_500,
    balance_before=500_000,
    transferred_this_month=0,
    approved_by_customer=False,
)


def test_transfer_within_mandate_is_allowed_by_clause_1() -> None:
    decision = check_action(MANDATE, ACTION)
    assert decision.allowed
    assert (decision.mandate_version, decision.clause) == (3, AUTHORISING_CLAUSE)


def test_paused_mandate_denies_everything() -> None:
    decision = check_action(replace(MANDATE, active=False), ACTION)
    assert not decision.allowed
    assert decision.clause == PAUSE_CLAUSE


def test_product_outside_mandate_is_denied() -> None:
    decision = check_action(MANDATE, replace(ACTION, product_id=1))
    assert (decision.allowed, decision.clause) == (False, AUTHORISING_CLAUSE)


def test_monthly_maximum_counts_earlier_transfers() -> None:
    decision = check_action(MANDATE, replace(ACTION, amount=10_000, transferred_this_month=70_000))
    assert (decision.allowed, decision.clause) == (False, AUTHORISING_CLAUSE)


def test_non_positive_amount_is_denied() -> None:
    assert not check_action(MANDATE, replace(ACTION, amount=0)).allowed


def test_balance_below_minimum_is_denied_by_clause_2() -> None:
    decision = check_action(MANDATE, replace(ACTION, balance_before=173_499))
    assert (decision.allowed, decision.clause) == (False, MIN_BALANCE_CLAUSE)


def test_leaving_exactly_the_minimum_is_allowed() -> None:
    assert check_action(MANDATE, replace(ACTION, balance_before=173_500)).allowed


def test_ac6_transfer_without_approval_is_denied_by_clause_3() -> None:
    mandate = replace(MANDATE, per_transfer_approval=True)
    decision = check_action(mandate, ACTION)
    assert (decision.allowed, decision.clause) == (False, APPROVAL_CLAUSE)
    assert check_action(mandate, replace(ACTION, approved_by_customer=True)).allowed


mandates = st.builds(
    MandateTerms,
    version=st.integers(min_value=1, max_value=10),
    active=st.booleans(),
    max_monthly_amount=st.integers(min_value=0, max_value=500_000),
    min_balance=st.integers(min_value=0, max_value=200_000),
    allowed_product_ids=st.frozensets(st.integers(min_value=1, max_value=5)),
    per_transfer_approval=st.booleans(),
)
actions = st.builds(
    TransferAction,
    product_id=st.integers(min_value=1, max_value=5),
    amount=st.integers(min_value=-1_000, max_value=500_000),
    balance_before=st.integers(min_value=-100_000, max_value=1_000_000),
    transferred_this_month=st.integers(min_value=0, max_value=500_000),
    approved_by_customer=st.booleans(),
)


@given(mandate=mandates, action=actions)
def test_allowed_transfer_respects_every_clause(
    mandate: MandateTerms, action: TransferAction
) -> None:
    decision = check_action(mandate, action)
    assert decision.mandate_version == mandate.version
    assert decision.clause in CLAUSES
    if decision.allowed:
        assert mandate.active
        assert action.amount > 0
        assert action.product_id in mandate.allowed_product_ids
        assert action.transferred_this_month + action.amount <= mandate.max_monthly_amount
        assert action.balance_before - action.amount >= mandate.min_balance
        assert action.approved_by_customer or not mandate.per_transfer_approval
