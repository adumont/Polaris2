import matplotlib

matplotlib.use("Agg")

from datetime import UTC, datetime

from polaris2.cartography import plot_chart
from polaris2.models import Fix, Position, Scenario, SightReduction


class TestPlotChart:
    def test_returns_figure_without_fix(self):
        scenario = Scenario(
            real_position=Position(lat=35.0, lon=-40.0),
            estimated_position=Position(lat=35.1, lon=-39.9),
            dr_error_nmi=5.0,
            utc=datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC),
            he_ft=10.0,
            fix=None,
        )
        fig = plot_chart(scenario)
        assert fig is not None

    def test_returns_figure_with_fix(self):
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
        fig = plot_chart(scenario)
        assert fig is not None

    def test_with_selected_reductions(self):
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
                    selected=True,
                ),
                SightReduction(
                    body_name="Moon",
                    hs=0.0,
                    ho=30.0,
                    hc=30.05,
                    intercept_nmi=-3.0,
                    azimut_zn=180.0,
                    lat_dr=35.1,
                    lon_dr=-39.9,
                    utc=datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC),
                    selected=False,
                ),
            ],
            fix=Fix(lat=35.05, lon=-39.95, error_nmi=2.5, iterations=3),
        )
        fig = plot_chart(scenario)
        assert fig is not None
