import pytest
from hypothesis import HealthCheck
from hypothesis import settings as hypothesis_settings
from pytest_django.fixtures import Settings

from core.clock import FixedClock
from tests.constants import TODAY

hypothesis_settings.register_profile(
    "saverai", suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
hypothesis_settings.load_profile("saverai")


@pytest.fixture(autouse=True)
def fixed_today(settings: Settings) -> None:
    """Every test runs on TODAY, also code that calls core.clock.get_clock()."""
    settings.SAVERAI_FIXED_DATE = TODAY.isoformat()


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock.on(TODAY)
