import pytest
from polaris2.core.almanac import body_alt_az, sun_alt_az, visible_bodies
from polaris2.models import Position
from datetime import datetime, timezone, UTC


class TestSunAltAz:
    def test_sun_returns_values(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        alt, az = sun_alt_az(dt, pos)
        assert isinstance(alt, float)
        assert isinstance(az, float)
        assert -90 <= alt <= 90
        assert 0 <= az <= 360


class TestBodyAltAz:
    def test_sun(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        alt, az = body_alt_az("Sun", dt, pos)
        assert isinstance(alt, float)

    def test_moon(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        alt, az = body_alt_az("Moon", dt, pos)
        assert isinstance(alt, float)

    def test_venus(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        alt, az = body_alt_az("Venus", dt, pos)
        assert isinstance(alt, float)
        assert -90 <= alt <= 90

    def test_mars(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        alt, az = body_alt_az("Mars", dt, pos)
        assert isinstance(alt, float)

    def test_jupiter(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        alt, az = body_alt_az("Jupiter", dt, pos)
        assert isinstance(alt, float)

    def test_saturn(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        alt, az = body_alt_az("Saturn", dt, pos)
        assert isinstance(alt, float)

    def test_unknown_raises(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        with pytest.raises(ValueError, match="Unknown body"):
            body_alt_az("Pluto", dt, pos)


class TestVisibleBodies:
    def test_sun_always_visible_daytime(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        vis = visible_bodies(dt, pos, 0.0)
        assert "Sun" in vis

    def test_includes_planets(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        vis = visible_bodies(dt, pos, 0.0)
        planet_names = {"Venus", "Mars", "Jupiter", "Saturn"}
        assert any(p in vis for p in planet_names)
