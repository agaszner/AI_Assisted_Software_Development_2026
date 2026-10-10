"""Plain input types of the rule engine."""

from dataclasses import dataclass
from datetime import date

from rules.money import Huf


@dataclass(frozen=True)
class Txn:
    booked_on: date
    amount: Huf  # positive: income, negative: expense
    own_transfer: bool = False  # between own accounts or a SaverAI savings transfer
    description: str = ""


@dataclass(frozen=True)
class ProductInfo:
    id: int
    name: str
    risk_level: int  # 1 (lowest) … 5
    min_horizon_months: int
    liquid: bool


@dataclass(frozen=True)
class PlannedExpense:
    name: str
    amount: Huf
    due_on: date
