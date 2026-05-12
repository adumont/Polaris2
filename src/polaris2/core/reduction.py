import math
from datetime import UTC, datetime

import numpy as np

from polaris2.config import EARTH_RADIUS_NMI, MIN_BODIES
from polaris2.core.almanac import body_alt_az
from polaris2.models import Fix, Position, Scenario, SightReduction


def compute_hc_zn(
    body_name: str,
    dt: datetime,
    dr_pos: Position,
    ho: float,
    hs: float = 0.0,
) -> SightReduction:
    alt, az = body_alt_az(body_name, dt, dr_pos, apparent=False)
    hc = alt
    zn = round(az, 1)
    intercept_nmi = round((ho - hc) * 60.0, 1)
    return SightReduction(
        body_name=body_name,
        hs=hs,
        ho=ho,
        hc=hc,
        intercept_nmi=intercept_nmi,
        azimut_zn=zn,
        lat_dr=dr_pos.lat,
        lon_dr=dr_pos.lon,
        utc=dt.replace(tzinfo=UTC),
    )


def solve_fix_least_squares(
    reductions: list[SightReduction],
    dr_pos: Position,
) -> Fix:
    lat = dr_pos.lat
    lon = dr_pos.lon
    mat = []
    vec = []
    for r in reductions:
        az_r = math.radians(r.azimut_zn)
        mat.append([math.cos(az_r), math.sin(az_r)])
        vec.append(r.intercept_nmi)
    if len(mat) < MIN_BODIES:
        return Fix(lat=lat, lon=lon, iterations=0)
    mat_arr = np.array(mat, dtype=float)
    vec_arr = np.array(vec, dtype=float)
    x, _, _, _ = np.linalg.lstsq(mat_arr, vec_arr, rcond=None)
    dlat_deg = float(x[0]) / 60.0
    dlon_deg = float(x[1]) / (60.0 * math.cos(math.radians(lat)))
    lat += dlat_deg
    lon += dlon_deg
    return Fix(lat=lat, lon=lon, iterations=1)


def solve_fix_single(reduction: SightReduction, dr_pos: Position) -> Fix:
    az_r = math.radians(reduction.azimut_zn)
    offset_deg = reduction.intercept_nmi / 60.0
    lat = dr_pos.lat + offset_deg * math.cos(az_r)
    lon = dr_pos.lon + offset_deg * math.sin(az_r) / math.cos(math.radians(dr_pos.lat))
    return Fix(lat=lat, lon=lon, iterations=1)


def recompute_fix(scenario: Scenario) -> None:
    selected = [r for r in scenario.sight_reductions if r.selected]
    if len(selected) == 0:
        scenario.fix = None
        return
    if len(selected) == 1:
        fix = solve_fix_single(selected[0], scenario.estimated_position)
    else:
        fix = solve_fix_least_squares(selected, scenario.estimated_position)
    fix = compute_fix_error(fix, scenario.real_position)
    scenario.fix = fix


def compute_fix_error(fix: Fix, real_pos: Position) -> Fix:
    dlat = math.radians(fix.lat - real_pos.lat)
    dlon = math.radians(fix.lon - real_pos.lon)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(real_pos.lat)) * math.cos(math.radians(fix.lat)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return Fix(lat=fix.lat, lon=fix.lon, error_nmi=c * EARTH_RADIUS_NMI, iterations=fix.iterations)
