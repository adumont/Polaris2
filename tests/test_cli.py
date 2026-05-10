import random
from polaris2.cli.app import run_scenario
from polaris2.config import DEFAULT_ERROR_NMI, DEFAULT_HE_FT


class TestRunScenario:
    def test_basic_run(self):
        random.seed(42)
        scenario = run_scenario(error_nmi=5.0, he_ft=10.0, seed=42)
        assert scenario.real_position is not None
        assert scenario.estimated_position is not None
        assert len(scenario.sextant_readings) >= 2
        assert len(scenario.sight_reductions) >= 2
        assert scenario.fix is not None
        assert scenario.fix.error_nmi is not None

    def test_different_seeds(self):
        s1 = run_scenario(seed=1)
        s2 = run_scenario(seed=2)
        assert s1.real_position.lat != s2.real_position.lat
