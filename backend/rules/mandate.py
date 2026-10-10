"""Mandate: the signed, versioned limits every order execution must pass (golden rule 6)."""

from dataclasses import dataclass

from rules.money import Huf

AUTHORISING_CLAUSE = 1
MIN_BALANCE_CLAUSE = 2
APPROVAL_CLAUSE = 3
PAUSE_CLAUSE = 4

CLAUSES: dict[int, str] = {
    AUTHORISING_CLAUSE: "SaverAI may transfer only to the products listed in this mandate, "
    "at most the monthly maximum in total per calendar month.",
    MIN_BALANCE_CLAUSE: "No transfer may leave the current account below the minimum balance.",
    APPROVAL_CLAUSE: "If per-transfer approval is set, each transfer needs the customer's "
    "explicit approval.",
    PAUSE_CLAUSE: "No transfer runs while the mandate is paused.",
}


@dataclass(frozen=True)
class MandateTerms:
    version: int
    active: bool
    max_monthly_amount: Huf
    min_balance: Huf
    allowed_product_ids: frozenset[int]
    per_transfer_approval: bool


@dataclass(frozen=True)
class TransferAction:
    product_id: int
    amount: Huf
    balance_before: Huf
    transferred_this_month: Huf  # already executed under this mandate this month
    approved_by_customer: bool


@dataclass(frozen=True)
class Decision:
    allowed: bool
    mandate_version: int
    clause: int  # the clause that allowed (1) or denied the transfer
    reason: str


def check_action(mandate: MandateTerms, action: TransferAction) -> Decision:
    """Allow or deny one transfer. Checks in order: pause (§4), products and monthly maximum (§1),
    minimum balance (§2), per-transfer approval (§3, last, so "awaiting approval" only happens
    when everything else is fine)."""

    def deny(clause: int, reason: str) -> Decision:
        return Decision(False, mandate.version, clause, reason)

    if not mandate.active:
        return deny(PAUSE_CLAUSE, "The mandate is paused.")
    if action.amount <= 0:
        return deny(AUTHORISING_CLAUSE, "The transfer amount must be positive.")
    if action.product_id not in mandate.allowed_product_ids:
        return deny(AUTHORISING_CLAUSE, "The product is not listed in the mandate.")
    if action.transferred_this_month + action.amount > mandate.max_monthly_amount:
        return deny(AUTHORISING_CLAUSE, "The monthly maximum would be exceeded.")
    if action.balance_before - action.amount < mandate.min_balance:
        return deny(MIN_BALANCE_CLAUSE, "The balance would drop below the minimum.")
    if mandate.per_transfer_approval and not action.approved_by_customer:
        return deny(APPROVAL_CLAUSE, "This transfer needs your approval.")
    return Decision(True, mandate.version, AUTHORISING_CLAUSE, "Within the mandate.")
