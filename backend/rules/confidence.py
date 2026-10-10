"""Confidence level from the amount of transaction data (AC6)."""

from enum import StrEnum

from rules.defaults import DEFAULTS, RuleParams


class Confidence(StrEnum):
    NONE = "none"  # too little data: no estimate, customer enters expected savings
    LOW = "low"
    NORMAL = "normal"


def assess_confidence(months_of_data: int, params: RuleParams = DEFAULTS) -> Confidence:
    """AC6: < min_months_for_estimate → NONE; < full_confidence_months → LOW; else NORMAL."""
    if months_of_data < params.min_months_for_estimate:
        return Confidence.NONE
    if months_of_data < params.full_confidence_months:
        return Confidence.LOW
    return Confidence.NORMAL


def needs_per_transfer_approval(confidence: Confidence) -> bool:
    """AC6: every transfer of a plan without normal confidence needs explicit approval."""
    return confidence is not Confidence.NORMAL
