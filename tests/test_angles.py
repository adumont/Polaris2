import math
import pytest
from polaris2.utils.angles import (
    deg_to_ddmmss,
    deg_to_ddmmmm,
    ddmmss_to_deg,
    ddmmmm_to_deg,
    parse_angle,
    body_label,
)


class TestDegToDDMMSS:
    def test_positive(self):
        result = deg_to_ddmmss(45.5)
        assert result == pytest.approx(453000.0, abs=0.1)

    def test_negative(self):
        result = deg_to_ddmmss(-45.5)
        assert result < 0

    def test_zero(self):
        result = deg_to_ddmmss(0)
        assert result == 0


class TestDegToDDMMMM:
    def test_positive(self):
        result = deg_to_ddmmmm(45.5)
        assert result == pytest.approx(453000.0, abs=0.1)

    def test_negative(self):
        result = deg_to_ddmmmm(-10.25)
        assert result < 0


class TestDDMMSSToDeg:
    def test_basic(self):
        result = ddmmss_to_deg(453000.0)
        assert result == pytest.approx(45.5, abs=1e-4)

    def test_negative(self):
        result = ddmmss_to_deg(-453000.0)
        assert result == pytest.approx(-45.5, abs=1e-4)


class TestDDMMMMToDeg:
    def test_basic(self):
        result = ddmmmm_to_deg(453000.0)
        assert result == pytest.approx(45.5, abs=1e-4)

    def test_negative(self):
        result = ddmmmm_to_deg(-102500.0)
        assert result == pytest.approx(-10.4167, abs=1e-4)


class TestRoundTrip:
    def test_ddmmss_roundtrip(self):
        original = 35.75
        converted = ddmmss_to_deg(deg_to_ddmmss(original))
        assert converted == pytest.approx(original, abs=1e-4)

    def test_ddmmmm_roundtrip(self):
        original = -20.5
        converted = ddmmmm_to_deg(deg_to_ddmmmm(original))
        assert converted == pytest.approx(original, abs=1e-4)


class TestParseAngle:
    def test_ddmmss(self):
        result = parse_angle(453000.0)
        assert result == pytest.approx(45.5, abs=1e-4)

    def test_ddmmmm(self):
        result = parse_angle(451500.0)
        assert result == pytest.approx(45.25, abs=1e-4)


class TestBodyLabel:
    def test_sun(self):
        assert body_label("Sun") == "Sun"

    def test_moon(self):
        assert body_label("Moon") == "Moon"

    def test_planet(self):
        assert body_label("Venus") == "Venus"
        assert body_label("Mars") == "Mars"
        assert body_label("Jupiter") == "Jupiter"
        assert body_label("Saturn") == "Saturn"

    def test_star_with_index(self):
        assert body_label("Antares") == "Antares (42)"
        assert body_label("Polaris") == "Polaris (0)"
        assert body_label("Sirius") == "Sirius (18)"

    def test_unknown(self):
        assert body_label("Foobar") == "Foobar"
