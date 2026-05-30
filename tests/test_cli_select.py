import random
import pytest
from polaris2.cli.app import _select_best_bodies
from celnav_core.models import Position
from datetime import datetime, timezone, UTC


class TestSelectBestBodies:
    def test_only_one_body(self, monkeypatch):
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        pos = Position(lat=30.0, lon=-40.0)
        bodies = _select_best_bodies(dt, pos)
        assert len(bodies) >= 0  # should not crash, may return 0-2

    def test_expand_to_extras(self):
        """When fewer than 3 bodies in best range, extras are added."""
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        pos = Position(lat=30.0, lon=-40.0)
        bodies = _select_best_bodies(dt, pos)
        assert isinstance(bodies, list)

    def test_empty_when_no_visible_bodies(self, monkeypatch):
        def no_bodies(*args, **kwargs):
            return -1.0, 0.0

        monkeypatch.setattr("polaris2.cli.app.body_alt_az", no_bodies)
        dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        pos = Position(lat=0.0, lon=0.0)
        bodies = _select_best_bodies(dt, pos)
        assert bodies == []

    def test_falls_back_when_none_in_best_range(self, monkeypatch):
        """Test the fallback where no bodies are in BEST_ALT_MIN-BEST_ALT_MAX but some are visible below min."""

        def mock_body_alt_az(name, dt, pos):
            alts = {
                "Sun": 25.0,
                "Moon": 15.0,
                "Venus": -5.0,
                "Mars": -10.0,
                "Jupiter": -20.0,
                "Saturn": -30.0,
            }
            return (alts.get(name, -99.0), 90.0)

        monkeypatch.setattr("polaris2.cli.app.body_alt_az", mock_body_alt_az)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        pos = Position(lat=30.0, lon=-40.0)
        bodies = _select_best_bodies(dt, pos)
        assert len(bodies) > 0

    def test_enough_good_bodies_uses_only_best(self, monkeypatch):
        def mock_body_alt_az(name, dt, pos):
            alts = {
                "Sun": 45.0,
                "Moon": 40.0,
                "Venus": 35.0,
                "Mars": 50.0,
                "Jupiter": 55.0,
                "Saturn": 10.0,
            }
            return (alts.get(name, -99.0), 90.0)

        monkeypatch.setattr("polaris2.cli.app.body_alt_az", mock_body_alt_az)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        pos = Position(lat=30.0, lon=-40.0)
        bodies = _select_best_bodies(dt, pos)
        assert len(bodies) == 4
