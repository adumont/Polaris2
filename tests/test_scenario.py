import math
import random
import pytest
from polaris2.models import Position
from polaris2.core.scenario import random_atlantic_position, dr_position


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
