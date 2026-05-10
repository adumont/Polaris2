import math

import matplotlib.pyplot as plt
import numpy as np

from polaris2.models import Position, Scenario
from polaris2.utils.angles import body_label

_HALF_CIRCLE = 180.0


def _nmi_offsets(lat: float, lon: float, ref: Position) -> tuple[float, float]:
    dy = (lat - ref.lat) * 60.0
    dx = (lon - ref.lon) * 60.0 * math.cos(math.radians(ref.lat))
    return dy, dx


def _plot_latlon_grid(ax, dr: Position, half: float, cx: float = 0, cy: float = 0):
    ylo = -half + cy
    yhi = half + cy
    xlo = -half + cx
    xhi = half + cx
    step = max(1.0, round(5.0 / math.cos(math.radians(dr.lat)) * 4) / 4)
    lat0 = round(dr.lat / step) * step
    lon0 = round(dr.lon / step) * step
    for lat_i in np.arange(lat0 - 10 * step, lat0 + 10 * step + 0.5 * step, step):
        offy, _ = _nmi_offsets(lat_i, dr.lon, dr)
        if ylo <= offy <= yhi:
            ax.axhline(offy, color="lightgray", linewidth=0.5)
            ax.text(xhi * 0.98, offy, f"{lat_i:.1f}°", fontsize=7, color="gray", ha="right", va="center")
    for lon_i in np.arange(lon0 - 10 * step, lon0 + 10 * step + 0.5 * step, step):
        _, offx = _nmi_offsets(dr.lat, lon_i, dr)
        if xlo <= offx <= xhi:
            ax.axvline(offx, color="lightgray", linewidth=0.5)
            ax.text(offx, yhi * 0.98, f"{lon_i:.1f}°", fontsize=7, color="gray", ha="center", va="top")


def _plot_lop(ax, red, color, half: float):
    az_r = math.radians(red.azimut_zn)
    offset = abs(red.alpha_nmi)
    if red.alpha_nmi < 0:
        cx = offset * math.sin(az_r)
        cy = offset * math.cos(az_r)
    else:
        cx = -offset * math.sin(az_r)
        cy = -offset * math.cos(az_r)
    ax.plot([0, cx], [0, cy], color=color, linewidth=1, linestyle=":")
    ax.plot(cx, cy, marker="o", color=color, markersize=5)
    hl = half * 2.5
    sx = cx + hl * math.cos(az_r)
    sy = cy - hl * math.sin(az_r)
    ex = cx - hl * math.cos(az_r)
    ey = cy + hl * math.sin(az_r)
    ax.plot([sx, ex], [sy, ey], color=color, linewidth=2, label=body_label(red.body_name))
    mx, my = (sx + ex) / 2, (sy + ey) / 2
    lw = half * 0.06
    ax.text(mx + lw, my + lw, body_label(red.body_name), color=color, fontweight="bold", fontsize=9)


def _plot_compass(ax, scenario: Scenario, half: float, colors, cx_shift: float = 0, cy_shift: float = 0):
    cx = half * 0.7 + cx_shift
    cy = half * 0.7 + cy_shift
    cr = half * 0.15
    ax.add_patch(plt.Circle((cx, cy), cr, fill=False, color="gray", linewidth=1))
    for angle_deg, label in [(0, "N"), (90, "E"), (_HALF_CIRCLE, "S"), (270, "W")]:
        a = math.radians(angle_deg)
        x = cx + cr * math.sin(a)
        y = cy + cr * math.cos(a)
        ax.plot(x, y, marker="+", color="gray", markersize=3)
        ax.text(
            cx + cr * 1.25 * math.sin(a),
            cy + cr * 1.25 * math.cos(a),
            label,
            color="gray",
            fontweight="bold",
            fontsize=8,
            ha="center",
            va="center",
        )
    selected = [r for r in scenario.sight_reductions if r.selected]
    for i, red in enumerate(selected):
        color = colors[i % len(colors)]
        a = math.radians(red.azimut_zn)
        tx = cx + cr * 0.85 * math.sin(a)
        ty = cy + cr * 0.85 * math.cos(a)
        ax.plot([cx, tx], [cy, ty], color=color, linewidth=2)
        label_angle = red.azimut_zn + 5 if red.azimut_zn < _HALF_CIRCLE else red.azimut_zn - 5
        la = math.radians(label_angle)
        ax.text(
            cx + cr * 1.4 * math.sin(la),
            cy + cr * 1.4 * math.cos(la),
            f"{body_label(red.body_name)} {red.azimut_zn:.0f}°",
            color=color,
            fontsize=7,
            fontweight="bold",
            ha="center",
            va="center",
        )


def plot_chart(scenario: Scenario, zoom: float = 1.5) -> plt.Figure:
    dr = scenario.estimated_position
    half = max(scenario.dr_error_nmi * zoom, 4.0)
    ry, rx = _nmi_offsets(scenario.real_position.lat, scenario.real_position.lon, dr)
    cx, cy = rx / 2, ry / 2
    colors = plt.cm.Set1.colors
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect("equal")
    ax.set_title("Navigation Chart (flat-plane)", fontsize=14, fontweight="bold")
    ax.set_xlabel("<-- West -- East --> (nmi)")
    ax.set_ylabel("<-- South -- North --> (nmi)")
    ax.set_xlim(-half + cx, half + cx)
    ax.set_ylim(-half + cy, half + cy)
    ax.grid(True, linestyle=":", alpha=0.3)
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.axvline(0, color="gray", linewidth=0.5)

    _plot_latlon_grid(ax, dr, half, cx, cy)
    selected = [r for r in scenario.sight_reductions if r.selected]
    for i, red in enumerate(selected):
        _plot_lop(ax, red, colors[i % len(colors)], half)

    off = half * 0.08
    ax.plot(0, 0, marker="s", color="blue", markersize=8, zorder=5)
    ax.text(off, off, "DR", color="blue", fontweight="bold", fontsize=10)
    ax.plot(rx, ry, marker="^", color="green", markersize=10, zorder=5)
    ax.text(rx + off, ry + off, "Real", color="green", fontweight="bold", fontsize=10)
    if scenario.fix:
        fy, fx = _nmi_offsets(scenario.fix.lat, scenario.fix.lon, dr)
        ax.plot(fx, fy, marker="D", color="red", markersize=10, zorder=5)
        ax.text(fx + off, fy + off, "Fix", color="red", fontweight="bold", fontsize=10)

    _plot_compass(ax, scenario, half, colors, cx, cy)
    ax.legend(loc="lower right", fontsize=9)
    plt.tight_layout()
    return fig
