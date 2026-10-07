"""Injected time source (AGENTS.md golden rule 5). The only module that reads the system clock."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from typing import Protocol

from django.conf import settings
from django.utils import timezone


class Clock(Protocol):
    def today(self) -> date: ...

    def now(self) -> datetime: ...


class SystemClock:
    def today(self) -> date:
        return timezone.localdate()

    def now(self) -> datetime:
        return timezone.now()


@dataclass(frozen=True)
class FixedClock:
    moment: datetime

    @classmethod
    def on(cls, day: date) -> "FixedClock":
        return cls(datetime.combine(day, time(12), tzinfo=UTC))

    def today(self) -> date:
        return self.moment.date()

    def now(self) -> datetime:
        return self.moment


def get_clock() -> Clock:
    """FixedClock when settings.SAVERAI_FIXED_DATE is set (demos, tests), otherwise SystemClock."""
    fixed = settings.SAVERAI_FIXED_DATE
    return FixedClock.on(date.fromisoformat(fixed)) if fixed else SystemClock()
