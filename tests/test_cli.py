import random
from datetime import UTC, datetime

import pytest

from polaris2.cli.app import _apply_selection, run_scenario
from polaris2.config import DEFAULT_ERROR_NMI, DEFAULT_HE_FT
from polaris2.core.reduction import recompute_fix
from polaris2.models import Position, Scenario, SightReduction


class TestRunScenario:
    def test_basic_run(self):
        random.seed(42)
        scenario = run_scenario(error_nmi=5.0, he_ft=10.0, seed=42)
        assert scenario.real_position is not None
        assert scenario.estimated_position is not None
        assert len(scenario.sextant_readings) >= 2
        assert len(scenario.sight_reductions) >= 2
        assert scenario.fix is None
        recompute_fix(scenario)
        assert scenario.fix is not None
        assert scenario.fix.error_nmi is not None

    def test_different_seeds(self):
        s1 = run_scenario(seed=1)
        s2 = run_scenario(seed=2)
        assert s1.real_position.lat != s2.real_position.lat


class TestApplySelection:
    dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)

    def make_scenario(self) -> Scenario:
        return Scenario(
            real_position=Position(lat=35.0, lon=-40.0),
            estimated_position=Position(lat=35.1, lon=-39.9),
            dr_error_nmi=5.0,
            utc=self.dt,
            he_ft=10.0,
            sight_reductions=[
                SightReduction(
                    body_name="Sun",
                    ho=45.0,
                    hc=45.1,
                    intercept_nmi=-6.0,
                    azimut_zn=90.0,
                    lat_dr=35.1,
                    lon_dr=-39.9,
                    utc=self.dt,
                ),
                SightReduction(
                    body_name="Moon",
                    ho=30.0,
                    hc=30.05,
                    intercept_nmi=-3.0,
                    azimut_zn=180.0,
                    lat_dr=35.1,
                    lon_dr=-39.9,
                    utc=self.dt,
                ),
                SightReduction(
                    body_name="Venus",
                    ho=20.0,
                    hc=20.05,
                    intercept_nmi=-3.0,
                    azimut_zn=45.0,
                    lat_dr=35.1,
                    lon_dr=-39.9,
                    utc=self.dt,
                ),
            ],
        )

    def test_all_selects_everything(self):
        s = self.make_scenario()
        _apply_selection(s, "all")
        assert all(r.selected for r in s.sight_reductions)

    def test_specific_indices(self):
        s = self.make_scenario()
        _apply_selection(s, "1,3")
        assert s.sight_reductions[0].selected
        assert not s.sight_reductions[1].selected
        assert s.sight_reductions[2].selected

    def test_invalid_index_ignored(self):
        s = self.make_scenario()
        _apply_selection(s, "999")
        assert not any(r.selected for r in s.sight_reductions)

    def test_zero_index_ignored(self):
        s = self.make_scenario()
        _apply_selection(s, "0")
        assert not any(r.selected for r in s.sight_reductions)

    def test_non_digit_ignored(self):
        s = self.make_scenario()
        _apply_selection(s, "abc")
        assert not any(r.selected for r in s.sight_reductions)
