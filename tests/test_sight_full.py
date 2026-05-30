import pytest
from celnav_core.core.sight import compute_ho, semidiameter_deg
from celnav_core.models import Position
from datetime import datetime, UTC


class TestComputeHo:
    def test_sun_ho(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        reading = compute_ho("Sun", dt, pos, 10.0)
        assert reading.body_name == "Sun"
        assert isinstance(reading.ho, float)
        assert reading.ho == reading.real_altitude

    def test_moon_lower_limb(self):
        sd = semidiameter_deg("Moon")
        assert sd > 0, "Moon must have semi-diameter > 0 for lower limb"

    def test_moon_ho(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        reading = compute_ho("Moon", dt, pos, 10.0)
        assert reading.body_name == "Moon"
        assert isinstance(reading.ho, float)
