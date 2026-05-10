import pytest
from polaris2.models import Position, SextantReading, SightReduction, Fix, Scenario
from datetime import datetime, timezone, UTC


class TestPosition:
    def test_create(self):
        p = Position(lat=35.5, lon=-40.2)
        assert p.lat == 35.5
        assert p.lon == -40.2

    def test_str_north_west(self):
        p = Position(lat=35.5, lon=-40.2)
        s = str(p)
        assert "N" in s
        assert "W" in s

    def test_str_south_east(self):
        p = Position(lat=-35.5, lon=40.2)
        s = str(p)
        assert "S" in s
        assert "E" in s


class TestSextantReading:
    def test_create(self):
        dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)
        r = SextantReading(body_name="Sun", ho=45.0, utc=dt, real_altitude=48.0, correction_total=-3.0)
        assert r.body_name == "Sun"
        assert r.ho == 45.0
        assert r.real_altitude == 48.0
        assert r.correction_total == -3.0


class TestSightReduction:
    def test_create(self):
        dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)
        r = SightReduction(
            body_name="Sun",
            ho=45.0,
            hc=45.1,
            intercept_nmi=-6.0,
            azimut_zn=180.0,
            lat_dr=30.0,
            lon_dr=-60.0,
            utc=dt,
        )
        assert r.body_name == "Sun"
        assert r.intercept_nmi == -6.0
        assert r.selected is True

    def test_selected_default_true(self):
        dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)
        r = SightReduction(
            body_name="Moon",
            ho=30.0,
            hc=30.1,
            intercept_nmi=-6.0,
            azimut_zn=90.0,
            lat_dr=30.0,
            lon_dr=-60.0,
            utc=dt,
        )
        assert r.selected is True

    def test_selected_can_be_false(self):
        dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)
        r = SightReduction(
            body_name="Venus",
            ho=20.0,
            hc=20.1,
            intercept_nmi=-6.0,
            azimut_zn=45.0,
            lat_dr=30.0,
            lon_dr=-60.0,
            utc=dt,
            selected=False,
        )
        assert r.selected is False


class TestFix:
    def test_create(self):
        f = Fix(lat=30.5, lon=-59.8, error_nmi=3.2, iterations=5)
        assert f.lat == 30.5
        assert f.error_nmi == 3.2
        assert f.iterations == 5


class TestScenario:
    def test_create_full(self):
        real = Position(lat=35.0, lon=-40.0)
        est = Position(lat=35.1, lon=-39.9)
        dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)
        reading = SextantReading(body_name="Sun", ho=45.0, utc=dt, real_altitude=48.0, correction_total=-3.0)
        reduction = SightReduction(
            body_name="Sun",
            ho=45.0,
            hc=45.1,
            intercept_nmi=-6.0,
            azimut_zn=180.0,
            lat_dr=35.1,
            lon_dr=-39.9,
            utc=dt,
        )
        fix = Fix(lat=35.05, lon=-39.95, error_nmi=2.0, iterations=4)
        scenario = Scenario(
            real_position=real,
            estimated_position=est,
            dr_error_nmi=5.0,
            utc=dt,
            he_ft=10.0,
            sextant_readings=[reading],
            sight_reductions=[reduction],
            fix=fix,
        )
        assert scenario.real_position.lat == 35.0
        assert scenario.dr_error_nmi == 5.0
        assert len(scenario.sextant_readings) == 1
        assert scenario.fix.lat == 35.05

    def test_create_minimal(self):
        real = Position(lat=35.0, lon=-40.0)
        est = Position(lat=35.1, lon=-39.9)
        dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)
        scenario = Scenario(real_position=real, estimated_position=est, dr_error_nmi=5.0, utc=dt, he_ft=10.0)
        assert scenario.fix is None
        assert scenario.sextant_readings == []
