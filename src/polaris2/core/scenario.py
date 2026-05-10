import math
import random
from datetime import UTC, datetime, timedelta

from skyfield.api import wgs84

from polaris2.config import EARTH_RADIUS_NMI
from polaris2.core.ephemeris import earth, ephemeris, timescale
from polaris2.models import Position


def _sun_above_horizon(pos: Position, dt: datetime) -> bool:
    t = timescale().from_datetime(dt.replace(tzinfo=UTC))
    obs = earth() + wgs84.latlon(pos.lat, pos.lon)
    astrometric = obs.at(t).observe(ephemeris()["sun"]).apparent()
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
    angle_rad = error_nmi / EARTH_RADIUS_NMI
    bearing = random.uniform(0, 2 * math.pi)
    lat1 = math.radians(real.lat)
    lon1 = math.radians(real.lon)
    lat2 = math.asin(math.sin(lat1) * math.cos(angle_rad) + math.cos(lat1) * math.sin(angle_rad) * math.cos(bearing))
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(angle_rad) * math.cos(lat1),
        math.cos(angle_rad) - math.sin(lat1) * math.sin(lat2),
    )
    return Position(lat=math.degrees(lat2), lon=math.degrees(lon2))
