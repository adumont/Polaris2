import pytest
from polaris2.utils.io import save_scenario, load_scenario
from celnav_core.models import Position, Scenario
from datetime import datetime, timezone, UTC
from pathlib import Path


class TestRoundTrip:
    def test_save_load(self, tmp_path):
        real = Position(lat=35.0, lon=-40.0)
        est = Position(lat=35.1, lon=-39.9)
        dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)
        scenario = Scenario(real_position=real, estimated_position=est, dr_error_nmi=5.0, utc=dt, he_ft=10.0)
        path = tmp_path / "test.yaml"
        save_scenario(scenario, path)
        loaded = load_scenario(path)
        assert loaded.real_position.lat == pytest.approx(35.0)
        assert loaded.real_position.lon == pytest.approx(-40.0)
        assert loaded.estimated_position.lat == pytest.approx(35.1)
        assert loaded.estimated_position.lon == pytest.approx(-39.9)
        assert loaded.dr_error_nmi == 5.0
        assert loaded.he_ft == 10.0
