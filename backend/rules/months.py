"""Calendar-month arithmetic. A month is represented by its first day."""

from datetime import date


def month_of(day: date) -> date:
    return day.replace(day=1)


def add_months(month: date, n: int) -> date:
    index = month.year * 12 + month.month - 1 + n
    return date(index // 12, index % 12 + 1, 1)


def months_between(start: date, end: date) -> int:
    """Whole calendar months from start's month to end's month (Oct → Aug next year = 10)."""
    return (end.year - start.year) * 12 + end.month - start.month
