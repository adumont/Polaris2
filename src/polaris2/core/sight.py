import math
from datetime import UTC, datetime

from polaris2.config import RADIOS_CUERPOS_KM
from polaris2.core.almanac import body_alt_az
from polaris2.models import Position, SextantReading


def dip_correction(he_ft: float) -> float:
    return -0.97 * math.sqrt(he_ft) / 60.0


def semidiameter_deg(body_name: str) -> float:
    radius_km = RADIOS_CUERPOS_KM.get(body_name)
    if radius_km is None:
        return 0.0
    is_sun = body_name in ("Sun", "Sol")
    distance_km = 149600000.0 if is_sun else 384400.0
    sd_rad = math.atan2(radius_km, distance_km)
    return math.degrees(sd_rad)


def compute_ho(
    body_name: str,
    dt: datetime,
    real_pos: Position,
    he_ft: float,
) -> SextantReading:
    apparent_alt, _ = body_alt_az(body_name, dt, real_pos)
    corr = dip_correction(he_ft)
    if body_name in ("Sun", "Moon"):
        corr += semidiameter_deg(body_name)
    return SextantReading(
        body_name=body_name,
        ho=apparent_alt,
        utc=dt.replace(tzinfo=UTC),
        real_altitude=apparent_alt,
        correction_total=corr,
    )
