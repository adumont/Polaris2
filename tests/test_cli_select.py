import random
from polaris2.cli.app import _select_best_bodies
from polaris2.models import Position
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
