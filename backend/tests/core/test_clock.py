from datetime import date

from pytest_django.fixtures import Settings

from core.clock import FixedClock, SystemClock, get_clock


def test_fixed_clock_returns_its_day() -> None:
    clock = FixedClock.on(date(2026, 10, 6))
    assert clock.today() == date(2026, 10, 6)
    assert clock.now().date() == date(2026, 10, 6)


def test_get_clock_uses_fixed_date_setting(settings: Settings) -> None:
    settings.SAVERAI_FIXED_DATE = "2026-01-31"
    assert get_clock().today() == date(2026, 1, 31)


def test_get_clock_without_setting_is_system_clock(settings: Settings) -> None:
    settings.SAVERAI_FIXED_DATE = None
    assert isinstance(get_clock(), SystemClock)
