import random
from contextlib import suppress

from textual import events, on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Header, Input, Label, RadioButton, RadioSet, Static

from polaris2.cli.app import run_scenario
from polaris2.config import DEFAULT_ERROR_NMI, DEFAULT_HE_FT
from polaris2.core.reduction import _SUGGEST_BEST, _SUGGEST_FALLBACK, recompute_fix, suggest_best_lops
from polaris2.models import Position, Scenario, SightReduction
from polaris2.utils.angles import body_label, format_angle, format_azimuth


class SightEditScreen(ModalScreen):
    CSS = """
    SightEditScreen {
        align: center middle;
    }
    #edit-dialog {
        width: 42;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #edit-dialog > Label {
        margin: 1 0 0 0;
    }
    #edit-dialog > Input {
        margin: 0 0 1 0;
    }
    #edit-dialog > Horizontal {
        height: auto;
        align: center middle;
    }
    """

    def __init__(self, reduction: SightReduction, label: str) -> None:
        super().__init__()
        self.reduction = reduction
        self.label = label

    def compose(self) -> ComposeResult:
        with Vertical(id="edit-dialog"):
            yield Label(f"Edit {self.label}")
            yield Label("Intercept I (nmi):")
            yield Input(value=f"{self.reduction.intercept_nmi:+.1f}", id="intercept-input")
            yield Label("Azimuth Zn (°):")
            yield Input(value=f"{self.reduction.azimut_zn:.1f}", id="azimuth-input")
            with Horizontal():
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", id="cancel-btn")

    @on(Button.Pressed, "#save-btn")
    def save(self) -> None:
        with suppress(ValueError):
            i = float(self.query_one("#intercept-input", Input).value)
            zn = float(self.query_one("#azimuth-input", Input).value)
            self.reduction.intercept_nmi = round(i, 1)
            self.reduction.azimut_zn = round(zn, 1)
            self.dismiss(True)

    @on(Button.Pressed, "#cancel-btn")
    def cancel(self) -> None:
        self.dismiss(False)


class Polaris2TUI(App):
    TITLE = "Polaris2 — Celestial Navigation"
    CSS_PATH = "polaris2.tcss"

    def __init__(self):
        super().__init__()
        self.scenario: Scenario | None = None
        self.fmt = "dms"

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            yield Static("Settings", classes="section-title")
            with Horizontal(classes="settings-row"):
                with Vertical(classes="setting-group"):
                    yield Label("DR Error (nmi)")
                    yield Input(str(DEFAULT_ERROR_NMI), id="error-input")
                with Vertical(classes="setting-group"):
                    yield Label("HE (ft)")
                    yield Input(str(DEFAULT_HE_FT), id="he-input")
                with Vertical(classes="setting-group"):
                    yield Label("Seed")
                    yield Input("42", id="seed-input")
                with Vertical(classes="setting-group"):
                    yield Label("Format")
                    yield RadioSet("DMS", "DMM", id="fmt-select")
                yield Button("Generate", id="gen-btn", variant="primary", classes="gen-btn")
            yield Static("", id="scenario-info", classes="info-panel")
            with Horizontal(classes="positions-row"):
                yield Static("Real: —", id="real-pos", classes="pos-card")
                yield Static("DR: —", id="dr-pos", classes="pos-card")
                yield Static("Fix: —", id="fix-pos", classes="pos-card")
            yield Static("Sextant Readings", classes="section-title")
            yield DataTable(id="readings-table", classes="data-table")
            yield Static("Sight Reductions", classes="section-title")
            yield DataTable(id="reductions-table", classes="data-table")
            with Horizontal():
                yield Button("Edit Sight Reduction", id="edit-btn", variant="default", disabled=True)
                yield Button("Recalculate Fix", id="recalc-btn", variant="default", disabled=True)
            yield Static("", id="fix-info", classes="info-panel")

    def on_mount(self) -> None:
        tbl = self.query_one("#readings-table", DataTable)
        tbl.add_columns("Body", "Hs", "Ho", "Corr (deg)")
        tbl = self.query_one("#reductions-table", DataTable)
        tbl.cursor_type = "row"
        tbl.add_columns(
            ("Use", "Use"),
            ("Body", "Body"),
            ("Hs", "Hs"),
            ("Hc", "Hc"),
            ("Ho", "Ho"),
            ("I (nmi)", "I (nmi)"),
            ("Zn", "Zn"),
        )

        self.query_one("#fmt-select", RadioSet)._selected = 0
        btn = self.query_one("#fmt-select", RadioSet).query(RadioButton).first()
        if btn:
            btn.value = True

    @on(Button.Pressed, "#gen-btn")
    def generate(self) -> None:
        try:
            error = float(self.query_one("#error-input", Input).value)
        except ValueError:
            error = DEFAULT_ERROR_NMI
        try:
            he = float(self.query_one("#he-input", Input).value)
        except ValueError:
            he = DEFAULT_HE_FT
        try:
            seed = int(self.query_one("#seed-input", Input).value)
        except ValueError:
            seed = None
        if seed is not None:
            random.seed(seed)
        scenario = run_scenario(error_nmi=error, he_ft=he, seed=seed)
        suggestion = suggest_best_lops(scenario.sight_reductions)
        if _SUGGEST_BEST in suggestion:
            indices, _ = suggestion[_SUGGEST_BEST]
            for i, r in enumerate(scenario.sight_reductions):
                r.selected = i in indices
        elif _SUGGEST_FALLBACK in suggestion:
            indices, _ = suggestion[_SUGGEST_FALLBACK]
            for i, r in enumerate(scenario.sight_reductions):
                r.selected = i in indices
        recompute_fix(scenario)
        self.scenario = scenario
        self.query_one("#recalc-btn", Button).disabled = False
        self.query_one("#edit-btn", Button).disabled = False
        self._update_all()

    @on(RadioSet.Changed, "#fmt-select")
    def on_format_change(self, event: RadioSet.Changed) -> None:
        self.fmt = "dmm" if str(event.pressed.label) == "DMM" else "dms"
        if self.scenario:
            self._update_all()

    def _toggle_row(self, row_idx: int) -> None:
        if not self.scenario or not (0 <= row_idx < len(self.scenario.sight_reductions)):
            return
        r = self.scenario.sight_reductions[row_idx]
        r.selected = not r.selected
        tbl = self.query_one("#reductions-table", DataTable)
        tbl.update_cell(str(row_idx), "Use", "X" if r.selected else " ")

    @on(events.Click, "#reductions-table")
    def on_reduction_click(self) -> None:
        tbl = self.query_one("#reductions-table", DataTable)
        if tbl.cursor_column == 0:
            self._toggle_row(tbl.cursor_row)

    @on(Button.Pressed, "#edit-btn")
    def edit_reduction(self) -> None:
        if not self.scenario:
            return
        row_idx = self.query_one("#reductions-table", DataTable).cursor_row
        if 0 <= row_idx < len(self.scenario.sight_reductions):
            r = self.scenario.sight_reductions[row_idx]
            self.push_screen(SightEditScreen(r, body_label(r.body_name)), self._on_edit_done)

    def _on_edit_done(self, result: bool | None) -> None:
        if result and self.scenario:
            self._update_reductions(self.scenario)

    @on(DataTable.RowSelected, "#reductions-table")
    def on_reduction_enter(self, event: DataTable.RowSelected) -> None:
        self._toggle_row(event.cursor_row)

    @on(Button.Pressed, "#recalc-btn")
    def recalculate_fix(self) -> None:
        if not self.scenario:
            return
        recompute_fix(self.scenario)
        self._update_positions(self.scenario)
        self._update_fix(self.scenario)

    def _update_all(self) -> None:
        s = self.scenario
        if not s:
            return
        self._update_info(s)
        self._update_positions(s)
        self._update_readings(s)
        self._update_reductions(s)
        self._update_fix(s)

    def _update_info(self, s: Scenario) -> None:
        self.query_one("#scenario-info", Static).update(
            f"UTC: {s.utc.strftime('%Y-%m-%d %H:%M:%S')} Z    DR Error: {s.dr_error_nmi:.1f} nmi"
        )

    def _update_positions(self, s: Scenario) -> None:
        self.query_one("#real-pos", Static).update(f"Real: {s.real_position.display(self.fmt)}")
        self.query_one("#dr-pos", Static).update(f"DR: {s.estimated_position.display(self.fmt)}")
        if s.fix:
            self.query_one("#fix-pos", Static).update(
                f"Fix: {Position(lat=s.fix.lat, lon=s.fix.lon).display(self.fmt)}"
            )
        else:
            self.query_one("#fix-pos", Static).update("Fix: —")

    def _update_readings(self, s: Scenario) -> None:
        tbl = self.query_one("#readings-table", DataTable)
        tbl.clear()
        for r in s.sextant_readings:
            tbl.add_row(
                body_label(r.body_name),
                format_angle(r.hs, self.fmt),
                format_angle(r.ho, self.fmt),
                f"{r.correction_total:+.4f}",
            )

    def _update_reductions(self, s: Scenario) -> None:
        tbl = self.query_one("#reductions-table", DataTable)
        tbl.clear()
        for i, r in enumerate(s.sight_reductions):
            tbl.add_row(
                "X" if r.selected else " ",
                body_label(r.body_name),
                format_angle(r.hs, self.fmt),
                format_angle(r.hc, self.fmt),
                format_angle(r.ho, self.fmt),
                f"{r.intercept_nmi:+.1f}",
                format_azimuth(r.azimut_zn),
                key=str(i),
            )

    def _update_fix(self, s: Scenario) -> None:
        if s.fix:
            self.query_one("#fix-info", Static).update(
                f"Fix: {Position(lat=s.fix.lat, lon=s.fix.lon).display(self.fmt)}  "
                f"Error: {s.fix.error_nmi:.2f} nmi  (iterations: {s.fix.iterations})"
            )
        else:
            self.query_one("#fix-info", Static).update("Not enough bodies for a fix (<2)")


def main():
    app = Polaris2TUI()
    app.run()


if __name__ == "__main__":
    main()
