import argparse
import random
from datetime import datetime

from polaris2.config import BEST_ALT_MAX, BEST_ALT_MIN, DEFAULT_ERROR_NMI, DEFAULT_HE_FT, NAVPAC_STAR_INDEX
from polaris2.core.almanac import body_alt_az
from polaris2.core.reduction import compute_fix_error, compute_hc_zn, solve_fix_least_squares
from polaris2.core.scenario import dr_position, random_daylight_datetime
from polaris2.core.sight import compute_ho
from polaris2.models import Position, Scenario
from polaris2.utils.angles import format_angle, format_ddmmss
from polaris2.utils.io import save_scenario

_MIN_VISIBLE_ALT = 0.0
_MIN_BODIES_FOR_FIX = 2
_MAX_SELECT = 3


def _visible_bodies_above(dt: datetime, pos: Position) -> dict[str, float]:
    names = ["Sun", "Moon"] + list(NAVPAC_STAR_INDEX)
    results = {}
    for name in names:
        try:
            alt, _ = body_alt_az(name, dt, pos)
            if alt > _MIN_VISIBLE_ALT:
                results[name] = alt
        except Exception:
            pass
    return results


def _select_best_bodies(dt: datetime, pos: Position) -> list[str]:
    all_vis = _visible_bodies_above(dt, pos)
    if not all_vis:
        return []
    good = [(alt, n) for n, alt in all_vis.items() if BEST_ALT_MIN <= alt <= BEST_ALT_MAX]
    good.sort(reverse=True)
    if len(good) >= _MAX_SELECT:
        return [n for _, n in good[:_MAX_SELECT]]
    extras = [(alt, n) for n, alt in all_vis.items() if n not in {n2 for _, n2 in good}]
    extras.sort(reverse=True)
    selected = [n for _, n in good] + [n for _, n in extras]
    return selected[:_MAX_SELECT] if len(selected) >= _MIN_BODIES_FOR_FIX else selected


def run_scenario(
    error_nmi: float = DEFAULT_ERROR_NMI,
    he_ft: float = DEFAULT_HE_FT,
    seed: int | None = None,
) -> Scenario:
    if seed is not None:
        random.seed(seed)
    for _attempt in range(10):
        dt, real_pos = random_daylight_datetime()
        dr = dr_position(real_pos, error_nmi)
        bodies = _select_best_bodies(dt, real_pos)
        if len(bodies) >= _MIN_BODIES_FOR_FIX:
            break
    scenario = Scenario(
        real_position=real_pos,
        estimated_position=dr,
        dr_error_nmi=error_nmi,
        utc=dt,
        he_ft=he_ft,
    )
    for name in bodies:
        reading = compute_ho(name, dt, real_pos, he_ft)
        scenario.sextant_readings.append(reading)
        reduction = compute_hc_zn(name, dt, dr, reading.ho)
        scenario.sight_reductions.append(reduction)
    if len(scenario.sight_reductions) >= _MIN_BODIES_FOR_FIX:
        fix = solve_fix_least_squares(scenario.sight_reductions, dr)
        fix = compute_fix_error(fix, real_pos)
        scenario.fix = fix
    return scenario


def main():
    parser = argparse.ArgumentParser(description="Celestial navigation scenario generator")
    parser.add_argument("--error", type=float, default=DEFAULT_ERROR_NMI, help="DR error in nmi")
    parser.add_argument("--he", type=float, default=DEFAULT_HE_FT, help="Height of eye in feet")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--output", type=str, default=None, help="Save scenario to YAML file")
    args = parser.parse_args()
    scenario = run_scenario(error_nmi=args.error, he_ft=args.he, seed=args.seed)
    print(f"UTC: {scenario.utc.strftime('%Y-%m-%d %H:%M:%S')} Z")
    print(f"Real Position:     {scenario.real_position}")
    print(f"DR Position:       {scenario.estimated_position}")
    print(f"DR Error:          {scenario.dr_error_nmi:.1f} nmi")
    print()
    print("Sextant Readings (real):")
    for r in scenario.sextant_readings:
        a = r.body_name
        print(
            f"  {a:12s}  Ho = {format_angle(r.ho)}  (alt = {format_angle(r.real_altitude)}, corr = {r.correction_total:+.4f} deg)"
        )
    print()
    print("Sight Reductions (from DR):")
    for r in scenario.sight_reductions:
        a = r.body_name
        print(
            f"  {a:12s}  Hc = {format_angle(r.hc)}  Ho = {format_angle(r.ho)}  alpha = {r.alpha_nmi:+.2f} nmi  Zn = {r.azimut_zn:.1f}° = {format_ddmmss(r.azimut_zn)}"
        )
    print()
    if scenario.fix:
        print(f"Fix Position:      {Position(lat=scenario.fix.lat, lon=scenario.fix.lon)}")
        print(f"Fix Error:         {scenario.fix.error_nmi:.2f} nmi  (iterations: {scenario.fix.iterations})")
    else:
        print("Not enough bodies for a fix (<2)")
    if args.output:
        save_scenario(scenario, args.output)
        print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
