import math
import random
from datetime import UTC, datetime

import pytest

from polaris2.core.scenario import dr_position, random_atlantic_position, random_daylight_datetime
from polaris2.models import Position


class TestDRPosition:
    def test_error_distance(self):
        real = Position(lat=30.0, lon=-40.0)
        dr = dr_position(real, 5.0)
        dlat = math.radians(dr.lat - real.lat)
        dlon = math.radians(dr.lon - real.lon)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(real.lat)) * math.cos(math.radians(dr.lat)) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance_nmi = c * 3440.065
        assert distance_nmi == pytest.approx(5.0, abs=0.1)

    def test_zero_error(self):
        real = Position(lat=30.0, lon=-40.0)
        dr = dr_position(real, 0.0)
        assert dr.lat == pytest.approx(real.lat, abs=1e-6)
        assert dr.lon == pytest.approx(real.lon, abs=1e-6)

    def test_reproducible_seed(self):
        real = Position(lat=30.0, lon=-40.0)
        random.seed(42)
        dr1 = dr_position(real, 5.0)
        random.seed(42)
        dr2 = dr_position(real, 5.0)
        assert dr1.lat == pytest.approx(dr2.lat)
        assert dr1.lon == pytest.approx(dr2.lon)


class TestRandomAtlanticPosition:
    def test_bounds(self):
        for _ in range(50):
            pos = random_atlantic_position()
            assert 10.0 <= pos.lat <= 50.0
            assert -80.0 <= pos.lon <= -10.0


class TestRandomDaylightDatetime:
    def test_returns_datetime_and_position(self):
        dt, pos = random_daylight_datetime()
        assert isinstance(dt, datetime)
        assert isinstance(pos, Position)

    def test_fallback_when_sun_never_above_horizon(self, monkeypatch):
        def never_above(*args, **kwargs):
            return False

        monkeypatch.setattr("polaris2.core.scenario._sun_above_horizon", never_above)
        dt, pos = random_daylight_datetime(max_attempts=5)
        assert dt == datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        assert pos.lat == 35.0
        assert pos.lon == -40.0
