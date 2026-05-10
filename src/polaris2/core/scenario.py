import math
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

from skyfield.api import Loader, wgs84

from polaris2.models import Position

_CACHE_DIR = Path.home() / ".polaris2" / "skyfield"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_LOAD = Loader(str(_CACHE_DIR))
_EPHEMERIS = _LOAD("de421.bsp")
_TS = _LOAD.timescale()
_EARTH = _EPHEMERIS["earth"]


def _sun_above_horizon(pos: Position, dt: datetime) -> bool:
    t = _TS.from_datetime(dt.replace(tzinfo=UTC))
    obs = _EARTH + wgs84.latlon(pos.lat, pos.lon)
    astrometric = obs.at(t).observe(_EPHEMERIS["sun"]).apparent()
    alt, _, _ = astrometric.altaz()
    return float(alt.degrees) > 0


def random_atlantic_position() -> Position:
    lat = random.uniform(10.0, 50.0)
    lon = random.uniform(-80.0, -10.0)
    return Position(lat=lat, lon=lon)


def random_daylight_datetime(max_attempts: int = 200) -> tuple[datetime, Position]:
    for _ in range(max_attempts):
        day = random.randint(1, 365)
        base = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=day - 1)
        hour = random.uniform(7, 19)
        minute_frac = (hour - int(hour)) * 60
        minute = int(minute_frac)
        second = int((minute_frac - minute) * 60)
        dt = base.replace(hour=int(hour), minute=minute, second=second)
        pos = random_atlantic_position()
        if _sun_above_horizon(pos, dt):
            return dt, pos
    dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
    return dt, Position(lat=35.0, lon=-40.0)


def dr_position(real: Position, error_nmi: float) -> Position:
    earth_radius_nmi = 3440.065
    angle_rad = error_nmi / earth_radius_nmi
    bearing = random.uniform(0, 2 * math.pi)
    lat1 = math.radians(real.lat)
    lon1 = math.radians(real.lon)
    lat2 = math.asin(math.sin(lat1) * math.cos(angle_rad) + math.cos(lat1) * math.sin(angle_rad) * math.cos(bearing))
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(angle_rad) * math.cos(lat1),
        math.cos(angle_rad) - math.sin(lat1) * math.sin(lat2),
    )
    return Position(lat=math.degrees(lat2), lon=math.degrees(lon2))
