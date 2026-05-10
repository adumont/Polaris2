import argparse
import random
from datetime import datetime

from polaris2.config import (
    BEST_ALT_MAX,
    BEST_ALT_MIN,
    DEFAULT_ERROR_NMI,
    DEFAULT_HE_FT,
    NAVPAC_STAR_INDEX,
    PLANET_BODIES,
)
from polaris2.core.almanac import body_alt_az
from polaris2.core.reduction import compute_hc_zn, recompute_fix
from polaris2.core.scenario import dr_position, random_daylight_datetime
from polaris2.core.sight import compute_ho
from polaris2.models import Position, Scenario
from polaris2.utils.angles import body_label, format_angle
from polaris2.utils.io import save_scenario

_MIN_VISIBLE_ALT = 0.0
_MIN_BODIES_FOR_FIX = 2
_MIN_BODIES_TARGET = 3
_MAX_SELECT = 4


def _visible_bodies_above(dt: datetime, pos: Position) -> dict[str, float]:
    names = ["Sun", "Moon"] + list(PLANET_BODIES) + list(NAVPAC_STAR_INDEX)
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
    for _attempt in range(20):
        dt, real_pos = random_daylight_datetime()
        dr = dr_position(real_pos, error_nmi)
        bodies = _select_best_bodies(dt, real_pos)
        if len(bodies) >= _MIN_BODIES_TARGET:
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
    return scenario


def _apply_selection(scenario: Scenario, choice: str) -> None:
    for r in scenario.sight_reductions:
        r.selected = False
    if choice.lower() == "all":
        for r in scenario.sight_reductions:
            r.selected = True
    else:
        parts = [p.strip() for p in choice.split(",")]
        for p in parts:
            if p.isdigit():
                idx = int(p) - 1
                if 0 <= idx < len(scenario.sight_reductions):
                    scenario.sight_reductions[idx].selected = True


def _interactive_select(scenario: Scenario, fmt: str) -> None:
    while True:
        print("\nSight Reductions:")
        for i, r in enumerate(scenario.sight_reductions):
            sel = "[x]" if r.selected else "[ ]"
            print(
                f"  {i + 1}. {sel} {body_label(r.body_name):12s}  a={r.alpha_nmi:+.2f}  Zn={format_angle(r.azimut_zn, fmt)}"
            )
        inp = input("\nEnter body numbers to use (comma-separated, e.g. '1,3,4') or 'all': ").strip()
        if not inp:
            break
        _apply_selection(scenario, inp)
        recompute_fix(scenario)
        print()
        if scenario.fix:
            print(f"Fix Position:      {Position(lat=scenario.fix.lat, lon=scenario.fix.lon).display(fmt)}")
            print(f"Fix Error:         {scenario.fix.error_nmi:.2f} nmi  (iterations: {scenario.fix.iterations})")
        else:
            print("Not enough selected bodies for a fix (<2)")
        again = input("\nAdjust selection? (y/n): ").strip().lower()
        if again != "y":
            break


def main():
    parser = argparse.ArgumentParser(description="Celestial navigation scenario generator")
    parser.add_argument("--error", type=float, default=DEFAULT_ERROR_NMI, help="DR error in nmi")
    parser.add_argument("--he", type=float, default=DEFAULT_HE_FT, help="Height of eye in feet")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument(
        "--format", type=str, choices=["dms", "dmm"], default="dms", help="Angle/position output format"
    )
    parser.add_argument("--output", type=str, default=None, help="Save scenario to YAML file")
    parser.add_argument("--interactive", action="store_true", help="Prompt to select which bodies to use for the fix")
    args = parser.parse_args()
    fmt = args.format
    scenario = run_scenario(error_nmi=args.error, he_ft=args.he, seed=args.seed)
    print(f"UTC: {scenario.utc.strftime('%Y-%m-%d %H:%M:%S')} Z")
    print(f"Real Position:     {scenario.real_position.display(fmt)}")
    print(f"DR Position:       {scenario.estimated_position.display(fmt)}")
    print(f"DR Error:          {scenario.dr_error_nmi:.1f} nmi")
    print()
    print("Sextant Readings (real):")
    for r in scenario.sextant_readings:
        a = body_label(r.body_name)
        print(
            f"  {a:12s}  Ho = {format_angle(r.ho, fmt)}  (alt = {format_angle(r.real_altitude, fmt)}, corr = {r.correction_total:+.4f} deg)"
        )
    print()
    print("Sight Reductions (from DR):")
    for r in scenario.sight_reductions:
        a = body_label(r.body_name)
        print(
            f"  {a:12s}  Hc = {format_angle(r.hc, fmt)}  Ho = {format_angle(r.ho, fmt)}  alpha = {r.alpha_nmi:+.2f} nmi  Zn = {format_angle(r.azimut_zn, fmt)}"
        )
    print()
    if args.interactive:
        _interactive_select(scenario, fmt)
    else:
        recompute_fix(scenario)
        if scenario.fix:
            print(f"Fix Position:      {Position(lat=scenario.fix.lat, lon=scenario.fix.lon).display(fmt)}")
            print(f"Fix Error:         {scenario.fix.error_nmi:.2f} nmi  (iterations: {scenario.fix.iterations})")
        else:
            print("Not enough bodies for a fix (<2)")
    if args.output:
        save_scenario(scenario, args.output)
        print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
