import pytest
from pytest_django.fixtures import Settings

from core.clock import FixedClock
from tests.constants import TODAY


@pytest.fixture(autouse=True)
def fixed_today(settings: Settings) -> None:
    """Every test runs on TODAY, also code that calls core.clock.get_clock()."""
    settings.SAVERAI_FIXED_DATE = TODAY.isoformat()


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock.on(TODAY)
