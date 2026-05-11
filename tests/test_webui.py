import subprocess
import sys
from datetime import UTC, datetime

from streamlit.testing.v1 import AppTest

from polaris2.models import Fix, Position, Scenario, SightReduction


class TestWebUI:
    def test_generate_scenario_button_present(self):
        at = AppTest.from_file("src/polaris2/webui/app.py", default_timeout=10)
        at.run(timeout=10)
        assert not at.exception
        assert len(at.button) >= 1

    def test_display_with_preset_scenario(self):
        scenario = Scenario(
            real_position=Position(lat=35.0, lon=-40.0),
            estimated_position=Position(lat=35.1, lon=-39.9),
            dr_error_nmi=5.0,
            utc=datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC),
            he_ft=10.0,
            sight_reductions=[
                SightReduction(
                    body_name="Sun",
                    hs=0.0,
                    ho=45.0,
                    hc=45.1,
                    intercept_nmi=-6.0,
                    azimut_zn=90.0,
                    lat_dr=35.1,
                    lon_dr=-39.9,
                    utc=datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC),
                ),
            ],
            fix=Fix(lat=35.05, lon=-39.95, error_nmi=2.5, iterations=3),
        )
        at = AppTest.from_file("src/polaris2/webui/app.py", default_timeout=10)
        at.session_state["scenario"] = scenario
        at.session_state["fmt"] = "dms"
        at.session_state["zoom"] = 1.5
        at.run(timeout=10)
        assert not at.exception

    def test_generate_and_show_scenario(self):
        at = AppTest.from_file("src/polaris2/webui/app.py", default_timeout=15)
        at.run(timeout=15)
        assert not at.exception
        btn = at.button
        assert len(btn) == 1
        btn[0].click().run(timeout=15)
        assert not at.exception

    def test_display_without_scenario_shows_info(self):
        at = AppTest.from_file("src/polaris2/webui/app.py", default_timeout=10)
        at.run(timeout=10)
        assert not at.exception
        assert len(at.info) >= 1

    def test_main_guard_via_subprocess(self):
        result = subprocess.run(
            [sys.executable, "-c", "from polaris2.webui.app import main; print('ok')"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert "ok" in result.stdout
