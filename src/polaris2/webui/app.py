import math

import folium
import streamlit as st
from streamlit_folium import st_folium

from polaris2.cli.app import run_scenario
from polaris2.config import DEFAULT_ERROR_NMI, DEFAULT_HE_FT
from polaris2.models import Position, Scenario


def _setup_page():
    st.set_page_config(
        page_title="Polaris2 — Celestial Navigation Simulator",
        layout="wide",
    )


def _controls() -> tuple[float, float, int | None]:
    col1, col2, col3 = st.columns(3)
    with col1:
        error = st.number_input("DR Error (nmi)", value=DEFAULT_ERROR_NMI, min_value=1.0, max_value=50.0, step=0.5)
    with col2:
        he = st.number_input("Height of Eye (ft)", value=DEFAULT_HE_FT, min_value=0.0, max_value=100.0, step=1.0)
    with col3:
        seed = st.number_input("Random Seed", value=42, min_value=0, step=1)
    return error, he, int(seed) if seed else None


def _draw_lop(sight, fix, dr, m):
    az_r = math.radians(sight.azimut_zn)
    alpha = sight.alpha_nmi
    nmi_per_deg = 60.0
    offset_deg = abs(alpha) / nmi_per_deg
    if alpha > 0:
        shift_lat = offset_deg * math.cos(az_r)
        shift_lon = offset_deg * math.sin(az_r) / math.cos(math.radians(dr.lat))
    else:
        shift_lat = -offset_deg * math.cos(az_r)
        shift_lon = -offset_deg * math.sin(az_r) / math.cos(math.radians(dr.lat))
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
        popup=f"{sight.body_name}: a={sight.alpha_nmi:+.1f} nmi, Zn={sight.azimut_zn:.0f} deg",
    ).add_to(m)


def _build_map(scenario: Scenario):
    center_lat = (scenario.real_position.lat + scenario.estimated_position.lat) / 2
    center_lon = (scenario.real_position.lon + scenario.estimated_position.lon) / 2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=5)
    folium.Marker(
        [scenario.real_position.lat, scenario.real_position.lon],
        popup=f"Real: {scenario.real_position}",
        icon=folium.Icon(color="green", icon="anchor", prefix="fa"),
    ).add_to(m)
    folium.Marker(
        [scenario.estimated_position.lat, scenario.estimated_position.lon],
        popup=f"DR: {scenario.estimated_position}",
        icon=folium.Icon(color="blue", icon="ship", prefix="fa"),
    ).add_to(m)
    if scenario.fix:
        folium.Marker(
            [scenario.fix.lat, scenario.fix.lon],
            popup=f"Fix: {Position(lat=scenario.fix.lat, lon=scenario.fix.lon)}<br>"
            f"Error: {scenario.fix.error_nmi:.2f} nmi",
            icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
        ).add_to(m)
    if scenario.sight_reductions and scenario.fix:
        dr = scenario.estimated_position
        for red in scenario.sight_reductions:
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


def _display(scenario: Scenario):
    st.subheader("Scenario")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("UTC", scenario.utc.strftime("%Y-%m-%d %H:%M Z"))
    c2.metric("Real Position", str(scenario.real_position))
    c3.metric("DR Position", str(scenario.estimated_position))
    c4.metric("DR Error", f"{scenario.dr_error_nmi:.1f} nmi")
    if scenario.fix:
        c1.metric("Fix Position", f"{Position(lat=scenario.fix.lat, lon=scenario.fix.lon)}")
        c2.metric("Fix Error", f"{scenario.fix.error_nmi:.2f} nmi")
    st.subheader("Sextant Readings")
    readings_data = []
    for r in scenario.sextant_readings:
        readings_data.append(
            {
                "Body": r.body_name,
                "Ho (deg)": f"{r.ho:.4f}",
                "Real Alt (deg)": f"{r.real_altitude:.4f}",
                "Correction (deg)": f"{r.correction_total:+.4f}",
            }
        )
    st.dataframe(readings_data, use_container_width=True)
    st.subheader("Sight Reductions")
    red_data = []
    for r in scenario.sight_reductions:
        red_data.append(
            {
                "Body": r.body_name,
                "Hc (deg)": f"{r.hc:.4f}",
                "Ho (deg)": f"{r.ho:.4f}",
                "a (nmi)": f"{r.alpha_nmi:+.2f}",
                "Zn (deg)": f"{r.azimut_zn:.1f}",
            }
        )
    st.dataframe(red_data, use_container_width=True)
    st.subheader("Map")
    if scenario.fix:
        c1, c2 = st.columns(2)
        c1.metric("Fix Lat", f"{scenario.fix.lat:.4f} deg")
        c2.metric("Fix Lon", f"{scenario.fix.lon:.4f} deg")
    m = _build_map(scenario)
    st_folium(m, width=None, height=600)


def main():
    _setup_page()
    st.title("Polaris2 - Celestial Navigation Simulator")
    st.markdown("Generate a realistic celestial navigation scenario with random real/DR positions and sight reduction.")
    with st.expander("Settings", expanded=True):
        error, he, seed = _controls()
    if st.button("Generate Scenario", type="primary"):
        scenario = run_scenario(error_nmi=error, he_ft=he, seed=seed)
        _display(scenario)
    else:
        st.info("Click **Generate Scenario** to start.")


if __name__ == "__main__":
    main()
