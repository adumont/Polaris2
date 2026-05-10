import math
import pytest
from polaris2.utils.angles import (
    _abs_deg_min,
    deg_to_ddmmss,
    deg_to_ddmmmm,
    ddmmss_to_deg,
    ddmmmm_to_deg,
    format_angle,
    format_azimuth,
    format_ddmmmm,
    format_ddmmss,
    format_position,
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

    def test_ddmmmm_when_rest_under_100(self):
        result = parse_angle(450030.0)
        assert result == pytest.approx(45.005, abs=1e-4)

    def test_negative_ddmmmm(self):
        result = parse_angle(-450030.0)
        assert result == pytest.approx(-45.005, abs=1e-4)


class TestFormatFunctions:
    def test_format_ddmmss(self):
        result = format_ddmmss(45.5)
        assert result == "45°30'00\""

    def test_format_ddmmmm(self):
        result = format_ddmmmm(45.5)
        assert result == "45°30.00'"

    def test_format_angle_default_dms(self):
        result = format_angle(45.5)
        assert result == "45°30'00\""

    def test_format_angle_dmm(self):
        result = format_angle(45.5, "dmm")
        assert result == "45°30.00'"

    def test_format_azimuth(self):
        result = format_azimuth(90.0)
        assert result == "90.0°"

    def test_format_position_default_dms(self):
        result = format_position(35.5, -40.25)
        assert "N" in result
        assert "W" in result

    def test_format_position_south_east(self):
        result = format_position(-35.5, 40.25)
        assert "S" in result
        assert "E" in result

    def test_format_position_dmm(self):
        result = format_position(35.5, -40.25, "dmm")
        assert "N" in result


class TestAbsDegMin:
    def test_returns_deg_and_min(self):
        d, m = _abs_deg_min(45.5)
        assert d == 45
        assert m == pytest.approx(30.0, abs=1e-4)

    def test_abs_deg_min_used_with_abs(self):
        d, m = _abs_deg_min(abs(-10.25))
        assert d == 10
        assert m == pytest.approx(15.0, abs=1e-4)


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
