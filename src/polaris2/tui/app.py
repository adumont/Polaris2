import random

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, DataTable, Header, Input, Label, Static

from polaris2.cli.app import run_scenario
from polaris2.config import DEFAULT_ERROR_NMI, DEFAULT_HE_FT
from polaris2.models import Position, Scenario
from polaris2.utils.angles import body_label, format_angle


class Polaris2TUI(App):
    TITLE = "Polaris2 — Celestial Navigation"
    CSS_PATH = "polaris2.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            yield Static("Settings", classes="section-title")
            yield Label("DR Error (nmi)")
            yield Input(str(DEFAULT_ERROR_NMI), id="error-input")
            yield Label("Height of Eye (ft)")
            yield Input(str(DEFAULT_HE_FT), id="he-input")
            yield Label("Seed")
            yield Input("42", id="seed-input")
            yield Button("Generate", id="gen-btn", variant="primary")
            yield Static("", id="scenario-info", classes="info-panel")
            with Horizontal(classes="positions-row"):
                yield Static("Real: —", id="real-pos", classes="pos-card")
                yield Static("DR: —", id="dr-pos", classes="pos-card")
                yield Static("Fix: —", id="fix-pos", classes="pos-card")
            yield Static("Sextant Readings", classes="section-title")
            yield DataTable(id="readings-table", classes="data-table")
            yield Static("Sight Reductions", classes="section-title")
            yield DataTable(id="reductions-table", classes="data-table")
            yield Static("", id="fix-info", classes="info-panel")

    def on_mount(self) -> None:
        tbl = self.query_one("#readings-table", DataTable)
        tbl.add_columns("Body", "Ho", "Real Alt", "Corr (deg)")
        tbl = self.query_one("#reductions-table", DataTable)
        tbl.add_columns("Body", "Hc", "Ho", "a (nmi)", "Zn")

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

        self._update_info(scenario)
        self._update_positions(scenario)
        self._update_readings(scenario)
        self._update_reductions(scenario)
        self._update_fix(scenario)

    def _update_info(self, s: Scenario) -> None:
        self.query_one("#scenario-info", Static).update(
            f"UTC: {s.utc.strftime('%Y-%m-%d %H:%M:%S')} Z    DR Error: {s.dr_error_nmi:.1f} nmi"
        )

    def _update_positions(self, s: Scenario) -> None:
        self.query_one("#real-pos", Static).update(f"Real: {s.real_position}")
        self.query_one("#dr-pos", Static).update(f"DR: {s.estimated_position}")
        if s.fix:
            self.query_one("#fix-pos", Static).update(f"Fix: {Position(lat=s.fix.lat, lon=s.fix.lon)}")
        else:
            self.query_one("#fix-pos", Static).update("Fix: —")

    def _update_readings(self, s: Scenario) -> None:
        tbl = self.query_one("#readings-table", DataTable)
        tbl.clear()
        for r in s.sextant_readings:
            tbl.add_row(
                body_label(r.body_name),
                format_angle(r.ho),
                format_angle(r.real_altitude),
                f"{r.correction_total:+.4f}",
            )

    def _update_reductions(self, s: Scenario) -> None:
        tbl = self.query_one("#reductions-table", DataTable)
        tbl.clear()
        for r in s.sight_reductions:
            tbl.add_row(
                body_label(r.body_name),
                format_angle(r.hc),
                format_angle(r.ho),
                f"{r.alpha_nmi:+.2f}",
                format_angle(r.azimut_zn),
            )

    def _update_fix(self, s: Scenario) -> None:
        if s.fix:
            self.query_one("#fix-info", Static).update(
                f"Fix Error: {s.fix.error_nmi:.2f} nmi  (iterations: {s.fix.iterations})"
            )
        else:
            self.query_one("#fix-info", Static).update("Not enough bodies for a fix (<2)")


def main():
    app = Polaris2TUI()
    app.run()


if __name__ == "__main__":
    main()
