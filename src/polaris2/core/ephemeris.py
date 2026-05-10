"""Lazy-loaded Skyfield ephemeris resources (shared, no import-time I/O)."""

from __future__ import annotations

from datetime import UTC, datetime
from functools import cache
from pathlib import Path

from skyfield.api import Loader, Star, wgs84
from skyfield.data import stellarium

from polaris2.config import NAVPAC_STAR_INDEX, PLANET_BODIES
from polaris2.utils.angles import round_to_arcsec

_CACHE_DIR = Path.home() / ".polaris2" / "skyfield"


def _ensure_cache_dir() -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


@cache
def _loader() -> Loader:
    _ensure_cache_dir()
    return Loader(str(_CACHE_DIR))


@cache
def ephemeris():
    return _loader()("de421.bsp")


@cache
def timescale():
    return _loader().timescale()


@cache
def earth():
    return ephemeris()["earth"]


@cache
def stars():
    with _loader().open("nabac.star") as f:
        return stellarium.parse_stellarium_enhanced(f)


def skyfield_star(name: str) -> Star:
    idx = NAVPAC_STAR_INDEX[name]
    row = stars().iloc[idx]
    return Star.from_data(row)


def body_alt_az(name: str, dt: datetime, pos) -> tuple[float, float]:
    t = timescale().from_datetime(dt.replace(tzinfo=UTC))
    observer = earth() + wgs84.latlon(pos.lat, pos.lon)
    if name == "Sun":
        body = ephemeris()["sun"]
    elif name == "Moon":
        body = ephemeris()["moon"]
    elif name in PLANET_BODIES:
        body = ephemeris()[PLANET_BODIES[name]]
    elif name in NAVPAC_STAR_INDEX:
        body = skyfield_star(name)
    else:
        msg = f"Unknown body: {name}"
        raise ValueError(msg)
    astrometric = observer.at(t).observe(body).apparent()
    alt, az, _ = astrometric.altaz()
    return round_to_arcsec(float(alt.degrees)), round_to_arcsec(float(az.degrees))
