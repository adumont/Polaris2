import asyncio
from datetime import UTC, datetime
import sys

import pytest

from textual.widgets import RadioSet, RadioButton

import polaris2.tui.app as tui_app
from polaris2.models import Fix, Position, Scenario, SightReduction
from polaris2.tui.app import Polaris2TUI, main


class TestTUIMain:
    def test_main_calls_app_run(self, monkeypatch):
        calls = []
        monkeypatch.setattr(Polaris2TUI, "run", lambda self: calls.append("run"))
        main()
        assert len(calls) == 1

    def test_module_imports(self):
        assert tui_app is not None

    def test_headless_compose(self):
        async def _run():
            app = Polaris2TUI()
            async with app.run_test(size=(80, 24)) as pilot:
                assert app.is_running
                pilot.app.exit()

        asyncio.run(_run())

    def test_headless_generate_and_recalculate(self):
        async def _run():
            app = Polaris2TUI()
            fake_scenario = Scenario(
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
            )
            async with app.run_test(size=(80, 24)) as pilot:
                orig_run = tui_app.run_scenario
                tui_app.run_scenario = lambda *a, **kw: fake_scenario
                try:
                    await pilot.click("#gen-btn")
                    await pilot.pause()
                    assert app.scenario is not None
                finally:
                    tui_app.run_scenario = orig_run
                pilot.app.exit()

        asyncio.run(_run())

    def test_headless_toggle_row(self):
        async def _run():
            app = Polaris2TUI()
            fake_scenario = Scenario(
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
            )
            async with app.run_test(size=(80, 24)) as pilot:
                orig_run = tui_app.run_scenario
                tui_app.run_scenario = lambda *a, **kw: fake_scenario
                try:
                    await pilot.click("#gen-btn")
                    await pilot.pause()
                    tbl = app.query_one("#reductions-table")
                    tbl.focus()
                    await pilot.pause()
                    assert app.scenario.sight_reductions[0].selected is True
                    await pilot.press("enter")
                    await pilot.pause()
                    assert app.scenario.sight_reductions[0].selected is False
                finally:
                    tui_app.run_scenario = orig_run
                pilot.app.exit()

        asyncio.run(_run())

    def test_headless_generate_with_invalid_inputs(self):
        async def _run():
            app = Polaris2TUI()
            fake_scenario = Scenario(
                real_position=Position(lat=35.0, lon=-40.0),
                estimated_position=Position(lat=35.1, lon=-39.9),
                dr_error_nmi=5.0,
                utc=datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC),
                he_ft=10.0,
            )
            async with app.run_test(size=(80, 24)) as pilot:
                orig_run = tui_app.run_scenario
                tui_app.run_scenario = lambda *a, **kw: fake_scenario
                try:
                    error_input = app.query_one("#error-input")
                    error_input.value = "not-a-number"
                    he_input = app.query_one("#he-input")
                    he_input.value = "also-invalid"
                    seed_input = app.query_one("#seed-input")
                    seed_input.value = "bad-seed"
                    await pilot.click("#gen-btn")
                    await pilot.pause()
                    assert app.scenario is not None
                finally:
                    tui_app.run_scenario = orig_run
                pilot.app.exit()

        asyncio.run(_run())


class TestPolaris2TUI:
    def test_update_info(self):
        app = Polaris2TUI()
        s = Scenario(
            real_position=Position(lat=35.0, lon=-40.0),
            estimated_position=Position(lat=35.1, lon=-39.9),
            dr_error_nmi=5.0,
            utc=__import__("datetime").datetime(2026, 6, 21, 12, 0, 0, tzinfo=__import__("datetime").timezone.utc),
            he_ft=10.0,
        )
        mock_static = type("MockStatic", (), {"update": lambda self, v: None})()
        app.query_one = lambda *a, **kw: mock_static
        app._update_info(s)

    def test_update_positions_without_fix(self):
        app = Polaris2TUI()
        s = Scenario(
            real_position=Position(lat=35.0, lon=-40.0),
            estimated_position=Position(lat=35.1, lon=-39.9),
            dr_error_nmi=5.0,
            utc=__import__("datetime").datetime(2026, 6, 21, 12, 0, 0, tzinfo=__import__("datetime").timezone.utc),
            he_ft=10.0,
        )
        updates = {}

        def mock_static_factory(which):
            class MockStatic:
                def update(self, v):
                    updates[which] = v

            return MockStatic()

        app.query_one = lambda selector, *_a: mock_static_factory(selector)
        app._update_positions(s)
        assert updates.get("#fix-pos") == "Fix: —"

    def test_update_reductions(self):
        app = Polaris2TUI()
        s = Scenario(
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
        )
        rows = []

        class MockDataTable:
            def clear(self):
                pass

            def add_row(self, *args, **kwargs):
                rows.append(args)

        app.query_one = lambda *a, **kw: MockDataTable()
        app._update_reductions(s)
        assert len(rows) == 1

    def test_update_fix_with_fix(self):
        app = Polaris2TUI()
        s = Scenario(
            real_position=Position(lat=35.0, lon=-40.0),
            estimated_position=Position(lat=35.1, lon=-39.9),
            dr_error_nmi=5.0,
            utc=__import__("datetime").datetime(2026, 6, 21, 12, 0, 0, tzinfo=__import__("datetime").timezone.utc),
            he_ft=10.0,
            fix=Fix(lat=35.05, lon=-39.95, error_nmi=2.5, iterations=3),
        )
        called = []

        class MockStatic:
            def update(self, v):
                called.append(v)

        app.query_one = lambda *a, **kw: MockStatic()
        app._update_fix(s)
        assert len(called) == 1

    def test_update_fix_without_fix(self):
        app = Polaris2TUI()
        s = Scenario(
            real_position=Position(lat=35.0, lon=-40.0),
            estimated_position=Position(lat=35.1, lon=-39.9),
            dr_error_nmi=5.0,
            utc=datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC),
            he_ft=10.0,
            fix=None,
        )
        called = []

        class MockStatic:
            def update(self, v):
                called.append(v)

        app.query_one = lambda *a, **kw: MockStatic()
        app._update_fix(s)
        assert len(called) == 1

    def test_update_positions_with_fix(self):
        app = Polaris2TUI()
        s = Scenario(
            real_position=Position(lat=35.0, lon=-40.0),
            estimated_position=Position(lat=35.1, lon=-39.9),
            dr_error_nmi=5.0,
            utc=datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC),
            he_ft=10.0,
            fix=Fix(lat=35.05, lon=-39.95, error_nmi=2.5, iterations=3),
        )
        updates = {}

        class MockStatic:
            def update(self, v):
                updates[id(self)] = v

        app.query_one = lambda *a, **kw: MockStatic()
        app._update_positions(s)
        assert any("Fix" in v for v in updates.values())

    def test_default_format_is_dms(self):
        app = Polaris2TUI()
        assert app.fmt == "dms"

    def test_format_change_sets_dmm(self):
        app = Polaris2TUI()
        mock_event = type("MockEvent", (), {"pressed": type("MockPressed", (), {"label": "DMM"})()})()
        app.on_format_change(mock_event)
        assert app.fmt == "dmm"

    def test_format_change_sets_dms(self):
        app = Polaris2TUI()
        app.fmt = "dmm"
        mock_event = type("MockEvent", (), {"pressed": type("MockPressed", (), {"label": "DMS"})()})()
        app.on_format_change(mock_event)
        assert app.fmt == "dms"

    def test_format_change_no_scenario_does_not_crash(self):
        app = Polaris2TUI()
        app.scenario = None
        mock_event = type("MockEvent", (), {"pressed": type("MockPressed", (), {"label": "DMM"})()})()
        app.on_format_change(mock_event)
        assert app.fmt == "dmm"

    def test_default_format_dms_selected(self):
        async def _run():
            app = Polaris2TUI()
            async with app.run_test(size=(80, 24)) as pilot:
                rs = app.query_one("#fmt-select", RadioSet)
                assert rs.pressed_index == 0
                pilot.app.exit()

        asyncio.run(_run())

    def test_update_readings(self):
        app = Polaris2TUI()
        s = Scenario(
            real_position=Position(lat=35.0, lon=-40.0),
            estimated_position=Position(lat=35.1, lon=-39.9),
            dr_error_nmi=5.0,
            utc=datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC),
            he_ft=10.0,
            sextant_readings=[
                __import__("polaris2.models", fromlist=["SextantReading"]).SextantReading(
                    body_name="Sun",
                    hs=45.0,
                    ho=45.0,
                    utc=datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC),
                    real_altitude=45.0,
                    correction_total=-0.016,
                ),
            ],
        )
        rows = []

        class MockDataTable:
            def clear(self):
                pass

            def add_row(self, *args, **kwargs):
                rows.append(args)

        app.query_one = lambda *a, **kw: MockDataTable()
        app._update_readings(s)
        assert len(rows) == 1
