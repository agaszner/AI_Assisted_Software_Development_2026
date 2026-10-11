"""Money type and the only rounding rules (AGENTS.md golden rule 3). Everything rounds down
to whole forints, except ceil_div, which is used where a target must be reached in time."""

from collections.abc import Sequence

Huf = int


def percent_of(amount: Huf, percent: int) -> Huf:
    """`percent` % of `amount`, rounded down."""
    return amount * percent // 100


def median(values: Sequence[Huf]) -> Huf:
    """Median; for an even count, the mean of the two middle values rounded down."""
    if not values:
        raise ValueError("median of an empty sequence")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) // 2


def ceil_div(amount: Huf, parts: int) -> Huf:
    """`amount` split into `parts`, rounded up, so that `parts` payments reach `amount`."""
    return -(-amount // parts)


def middle_values(values: Sequence[Huf]) -> tuple[Huf, ...]:
    """The value(s) `median` uses: one for an odd count, two for an even count."""
    if not values:
        raise ValueError("middle values of an empty sequence")
    ordered = sorted(values)
    middle = len(ordered) // 2
    return (ordered[middle],) if len(ordered) % 2 else (ordered[middle - 1], ordered[middle])


def progress_percent(saved: Huf, target: Huf) -> int:
    """Whole percent of `target` reached, rounded down, at most 100. `target` must be positive."""
    return min(100, saved * 100 // target)
