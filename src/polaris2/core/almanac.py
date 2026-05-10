from datetime import UTC, datetime
from pathlib import Path

from skyfield.api import Loader, Star, wgs84
from skyfield.data import stellarium

from polaris2.config import NAVPAC_STAR_INDEX
from polaris2.models import Position
from polaris2.utils.angles import round_to_arcsec

_CACHE_DIR = Path.home() / ".polaris2" / "skyfield"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_LOAD = Loader(str(_CACHE_DIR))
_EPHEMERIS = _LOAD("de421.bsp")
_TS = _LOAD.timescale()
_EARTH = _EPHEMERIS["earth"]
_STARS = None


def _get_stars():
    global _STARS
    if _STARS is None:
        with _LOAD.open("nabac.star") as f:
            _STARS = stellarium.parse_stellarium_enhanced(f)
    return _STARS


def _skyfield_star(name: str) -> Star:
    stars = _get_stars()
    idx = NAVPAC_STAR_INDEX[name]
    row = stars.iloc[idx]
    return Star.from_data(row)


def body_alt_az(name: str, dt: datetime, pos: Position) -> tuple[float, float]:
    t = _TS.from_datetime(dt.replace(tzinfo=UTC))
    observer = _EARTH + wgs84.latlon(pos.lat, pos.lon)
    if name == "Sun":
        body = _EPHEMERIS["sun"]
    elif name == "Moon":
        body = _EPHEMERIS["moon"]
    elif name in NAVPAC_STAR_INDEX:
        body = _skyfield_star(name)
    else:
        msg = f"Unknown body: {name}"
        raise ValueError(msg)
    astrometric = observer.at(t).observe(body).apparent()
    alt, az, _ = astrometric.altaz()
    return round_to_arcsec(float(alt.degrees)), round_to_arcsec(float(az.degrees))


def body_alt_az_multiple(names: list[str], dt: datetime, pos: Position) -> dict[str, tuple[float, float]]:
    return {n: body_alt_az(n, dt, pos) for n in names}


def sun_alt_az(dt: datetime, pos: Position) -> tuple[float, float]:
    return body_alt_az("Sun", dt, pos)


def moon_alt_az(dt: datetime, pos: Position) -> tuple[float, float]:
    return body_alt_az("Moon", dt, pos)


def visible_bodies(dt: datetime, pos: Position, min_alt: float = 10.0) -> list[str]:
    result = []
    try:
        alt_sun, _ = sun_alt_az(dt, pos)
        if alt_sun > min_alt:
            result.append("Sun")
    except Exception:
        pass
    try:
        alt_moon, _ = moon_alt_az(dt, pos)
        if alt_moon > min_alt:
            result.append("Moon")
    except Exception:
        pass
    for name in NAVPAC_STAR_INDEX:
        try:
            alt, _ = body_alt_az(name, dt, pos)
            if alt > min_alt:
                result.append(name)
        except Exception:
            pass
    return result
