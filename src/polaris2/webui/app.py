import math
import random

import folium
import streamlit as st
from streamlit_folium import st_folium

from polaris2.cartography import plot_chart
from polaris2.cli.app import run_scenario
from polaris2.config import DEFAULT_ERROR_NMI, DEFAULT_HE_FT
from polaris2.core.reduction import recompute_fix
from polaris2.models import Position, Scenario
from polaris2.utils.angles import body_label, format_angle, format_azimuth


def _setup_page():
    st.set_page_config(
        page_title="Polaris2 — Celestial Navigation Simulator",
        layout="wide",
    )


def _controls() -> tuple[float, float, int | None, str, float]:
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        error = st.number_input("DR Error (nmi)", value=DEFAULT_ERROR_NMI, min_value=1.0, max_value=50.0, step=0.5)
    with col2:
        he = st.number_input("Height of Eye (ft)", value=DEFAULT_HE_FT, min_value=0.0, max_value=100.0, step=1.0)
    with col3:
        seed_str = st.text_input("Random Seed (empty for random)", value=st.session_state.get("seed_value", ""))
    with col4:
        fmt = st.radio("Angle Format", options=["dms", "dmm"], horizontal=True)
    with col5:
        zoom = st.slider("Chart Zoom", min_value=0.1, max_value=3.0, value=1.5, step=0.1)
    return error, he, int(seed_str) if seed_str.strip() else None, fmt, zoom


def _draw_lop(sight, fix, dr, m):
    az_r = math.radians(sight.azimut_zn)
    intercept = sight.intercept_nmi
    nmi_per_deg = 60.0
    offset_deg = intercept / nmi_per_deg
    shift_lat = offset_deg * math.cos(az_r)
    shift_lon = offset_deg * math.sin(az_r) / math.cos(math.radians(dr.lat))
    lop_lat = dr.lat + shift_lat
    lop_lon = dr.lon + shift_lon
    perp_az = az_r + math.pi / 2
    half_extent = 2.0
    p1_lat = lop_lat + half_extent * math.cos(perp_az)
    p1_lon = lop_lon + half_extent * math.sin(perp_az) / math.cos(math.radians(lop_lat))
    p2_lat = lop_lat - half_extent * math.cos(perp_az)
    p2_lon = lop_lon - half_extent * math.sin(perp_az) / math.cos(math.radians(lop_lat))
    color = "#e74c3c"
    folium.PolyLine(
        locations=[(p1_lat, p1_lon), (p2_lat, p2_lon)],
        color=color,
        weight=2,
        opacity=0.8,
        popup=f"{body_label(sight.body_name)}: I={sight.intercept_nmi:+.1f} nmi, Zn={format_azimuth(sight.azimut_zn)}",
    ).add_to(m)


def _build_map(scenario: Scenario, fmt: str = "dms"):
    center_lat = (scenario.real_position.lat + scenario.estimated_position.lat) / 2
    center_lon = (scenario.real_position.lon + scenario.estimated_position.lon) / 2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=5)
    folium.Marker(
        [scenario.real_position.lat, scenario.real_position.lon],
        popup=f"Real: {scenario.real_position.display(fmt)}",
        icon=folium.Icon(color="green", icon="anchor", prefix="fa"),
    ).add_to(m)
    folium.Marker(
        [scenario.estimated_position.lat, scenario.estimated_position.lon],
        popup=f"DR: {scenario.estimated_position.display(fmt)}",
        icon=folium.Icon(color="blue", icon="ship", prefix="fa"),
    ).add_to(m)
    if scenario.fix:
        folium.Marker(
            [scenario.fix.lat, scenario.fix.lon],
            popup=f"Fix: {Position(lat=scenario.fix.lat, lon=scenario.fix.lon).display(fmt)}<br>"
            f"Error: {scenario.fix.error_nmi:.2f} nmi",
            icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
        ).add_to(m)
    if scenario.sight_reductions and scenario.fix:
        dr = scenario.estimated_position
        for red in scenario.sight_reductions:
            if red.selected:
                _draw_lop(red, scenario.fix, dr, m)
    error_line = [
        (scenario.real_position.lat, scenario.real_position.lon),
        (scenario.estimated_position.lat, scenario.estimated_position.lon),
    ]
    folium.PolyLine(
        locations=error_line,
        color="gray",
        weight=1,
        dash_array="5,5",
        popup=f"DR Error: {scenario.dr_error_nmi:.1f} nmi",
    ).add_to(m)
    if scenario.fix:
        fix_error_line = [
            (scenario.real_position.lat, scenario.real_position.lon),
            (scenario.fix.lat, scenario.fix.lon),
        ]
        folium.PolyLine(
            locations=fix_error_line,
            color="orange",
            weight=1,
            dash_array="3,3",
            popup=f"Fix Error: {scenario.fix.error_nmi:.2f} nmi",
        ).add_to(m)
    return m


def _display(scenario: Scenario, fmt: str = "dms", zoom: float = 1.5):
    st.subheader("Scenario")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("UTC", scenario.utc.strftime("%Y-%m-%d %H:%M:%S Z"))
    c2.metric("Real Position", scenario.real_position.display(fmt))
    c3.metric("DR Position", scenario.estimated_position.display(fmt))
    c4.metric("DR Error", f"{scenario.dr_error_nmi:.1f} nmi")
    st.subheader("Sextant Readings")
    readings_data = []
    for r in scenario.sextant_readings:
        readings_data.append(
            {
                "Body": body_label(r.body_name),
                "Hs": format_angle(r.hs, fmt),
                "Ho": format_angle(r.ho, fmt),
                "Corr (deg)": f"{r.correction_total:+.4f}",
            }
        )
    st.dataframe(readings_data, width="stretch")
    st.subheader("Sight Reductions")
    red_data = []
    for i, r in enumerate(scenario.sight_reductions):
        red_data.append(
            {
                "idx": i,
                "selected": r.selected,
                "Body": body_label(r.body_name),
                "Hs": format_angle(r.hs, fmt),
                "Hc": format_angle(r.hc, fmt),
                "Ho": format_angle(r.ho, fmt),
                "I (nmi)": f"{r.intercept_nmi:+.1f}",
                "Zn": format_azimuth(r.azimut_zn),
            }
        )
    edited = st.data_editor(
        red_data,
        column_config={
            "idx": None,
            "selected": st.column_config.CheckboxColumn("Use"),
            "Body": "Body",
            "Hc": "Hc",
            "Ho": "Ho",
            "I (nmi)": "I (nmi)",
            "Zn": "Zn",
        },
        disabled=["idx", "Body", "Hs", "Hc", "Ho", "I (nmi)", "Zn"],
        hide_index=True,
    )
    st.caption(
        "**Hs** = Sextant altitude (raw) · "
        "**Hc** = Computed altitude at DR · "
        "**Ho** = Observed altitude at real position · "
        "**I (nmi)** = Intercept (Ho − Hc, positive = Toward body) · "
        "**Zn** = Azimuth of body"
    )
    if st.button("Recalculate Fix"):
        for row in edited:
            scenario.sight_reductions[row["idx"]].selected = row["selected"]
        recompute_fix(scenario)
        st.rerun()
    st.subheader("Charts")
    if scenario.fix:
        cc1, cc2 = st.columns(2)
        cc1.metric("Fix Position", f"{Position(lat=scenario.fix.lat, lon=scenario.fix.lon).display(fmt)}")
        cc2.metric("Fix Error", f"{scenario.fix.error_nmi:.2f} nmi")
    col_map, col_chart = st.columns(2)
    with col_map:
        m = _build_map(scenario, fmt)
        st_folium(m, width=None, height=600)
    with col_chart:
        fig = plot_chart(scenario, zoom=zoom)
        st.pyplot(fig)


def main():
    _setup_page()
    st.title("Polaris2 - Celestial Navigation Simulator")
    st.markdown("Generate a realistic celestial navigation scenario with random real/DR positions and sight reduction.")
    with st.expander("Settings", expanded=True):
        error, he, seed, fmt, zoom = _controls()
    if st.button("Generate Scenario", type="primary"):
        if seed is None:
            seed = random.getrandbits(63)
        st.session_state.seed_value = str(seed)
        st.session_state.scenario = run_scenario(error_nmi=error, he_ft=he, seed=seed)
        st.session_state.fmt = fmt
        st.session_state.zoom = zoom
    if "scenario" in st.session_state:
        _display(st.session_state.scenario, st.session_state.fmt, st.session_state.get("zoom", 1.5))
    else:
        st.info("Click **Generate Scenario** to start.")


if __name__ == "__main__":
    main()
