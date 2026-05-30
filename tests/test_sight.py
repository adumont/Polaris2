import pytest
from celnav_core.core.sight import dip_correction, semidiameter_deg


class TestDipCorrection:
    def test_positive_he(self):
        corr = dip_correction(10.0)
        assert corr < 0

    def test_zero_he(self):
        corr = dip_correction(0.0)
        assert abs(corr) < 1e-6

    def test_increasing_with_he(self):
        c1 = abs(dip_correction(10.0))
        c2 = abs(dip_correction(20.0))
        assert c2 > c1


class TestSemidiameter:
    def test_sun(self):
        sd = semidiameter_deg("Sun")
        assert sd > 0.25
        assert sd < 0.28

    def test_moon(self):
        sd = semidiameter_deg("Moon")
        assert sd > 0.2
        assert sd < 0.3

    def test_star(self):
        sd = semidiameter_deg("Sirius")
        assert sd == 0.0
