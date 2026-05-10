"""Public celestial navigation API — delegates Skyfield work to `ephemeris`."""

from datetime import datetime

from polaris2.config import NAVPAC_STAR_INDEX, PLANET_BODIES
from polaris2.core.ephemeris import body_alt_az
from polaris2.models import Position


def body_alt_az_multiple(names: list[str], dt: datetime, pos: Position) -> dict[str, tuple[float, float]]:
    return {n: body_alt_az(n, dt, pos) for n in names}


def sun_alt_az(dt: datetime, pos: Position) -> tuple[float, float]:
    return body_alt_az("Sun", dt, pos)


def moon_alt_az(dt: datetime, pos: Position) -> tuple[float, float]:
    return body_alt_az("Moon", dt, pos)


def visible_bodies(dt: datetime, pos: Position, min_alt: float = 10.0) -> list[str]:
    result = []
    for name in ["Sun", "Moon"] + list(PLANET_BODIES) + list(NAVPAC_STAR_INDEX):
        try:
            alt, _ = body_alt_az(name, dt, pos)
            if alt > min_alt:
                result.append(name)
        except Exception:
            pass
    return result
