import pytest
from polaris2.utils.angles import parse_angle


class TestParseAngleEdgeCases:
    def test_ddmmmm_format(self):
        result = parse_angle(451500.0)
        assert isinstance(result, float)

    def test_negative_ddmmss(self):
        result = parse_angle(-453000.0)
        assert result < 0
