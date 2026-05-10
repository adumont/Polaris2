import math
import pytest
from polaris2.models import Position, SightReduction, Fix
from polaris2.core.reduction import compute_fix_error, solve_fix_least_squares
from datetime import datetime, timezone, UTC


class TestComputeFixError:
    def test_zero_error(self):
        pos = Position(lat=30.0, lon=-40.0)
        fix = Fix(lat=30.0, lon=-40.0)
        fix = compute_fix_error(fix, pos)
        assert fix.error_nmi == pytest.approx(0.0, abs=1e-4)

    def test_one_degree_lat(self):
        pos = Position(lat=30.0, lon=-40.0)
        fix = Fix(lat=31.0, lon=-40.0)
        fix = compute_fix_error(fix, pos)
        assert fix.error_nmi == pytest.approx(60.0, abs=0.1)


class TestSolveFixLeastSquares:
    def test_two_reductions(self):
        dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)
        reductions = [
            SightReduction(
                body_name="Sun",
                ho=45.0,
                hc=45.1,
                alpha_nmi=6.0,
                azimut_zn=90.0,
                lat_dr=30.0,
                lon_dr=-40.0,
                utc=dt,
            ),
            SightReduction(
                body_name="Moon",
                ho=30.0,
                hc=30.05,
                alpha_nmi=3.0,
                azimut_zn=180.0,
                lat_dr=30.0,
                lon_dr=-40.0,
                utc=dt,
            ),
        ]
        dr = Position(lat=30.0, lon=-40.0)
        fix = solve_fix_least_squares(reductions, dr)
        assert isinstance(fix.lat, float)
        assert isinstance(fix.lon, float)
        assert fix.iterations >= 1
