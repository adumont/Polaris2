from polaris2.config import NAVPAC_STAR_INDEX, PLANET_BODIES


def deg_to_ddmmss(value: float) -> float:
    sign = -1 if value < 0 else 1
    v = abs(value)
    d = int(v)
    m = int((v - d) * 60)
    s = (v - d - m / 60) * 3600
    return sign * (d * 10000 + m * 100 + s)


def deg_to_ddmmmm(value: float) -> float:
    sign = -1 if value < 0 else 1
    v = abs(value)
    d = int(v)
    mm = (v - d) * 60
    return sign * (d * 10000 + mm * 100)


def ddmmss_to_deg(value: float) -> float:
    sign = -1 if value < 0 else 1
    v = abs(value)
    d = int(v // 10000)
    m = int((v - d * 10000) // 100)
    s = v - d * 10000 - m * 100
    return sign * (d + m / 60 + s / 3600)


def ddmmmm_to_deg(value: float) -> float:
    sign = -1 if value < 0 else 1
    v = abs(value)
    d = int(v // 10000)
    mm = (v - d * 10000) / 100
    return sign * (d + mm / 60)


def round_to_arcsec(deg: float) -> float:
    v = abs(deg)
    d = int(v)
    m = int((v - d) * 60)
    s = round((v - d - m / 60) * 3600)
    return (1 if deg >= 0 else -1) * (d + m / 60 + s / 3600)


def parse_angle(value: float) -> float:
    v = abs(value)
    d = int(v // 10000)
    rest = v - d * 10000
    if rest > 100.0:  # noqa: PLR2004
        return ddmmss_to_deg(value)
    else:
        return ddmmmm_to_deg(value)


def _abs_deg_min_sec(v: float) -> tuple[int, int, float]:
    d = int(v)
    m = int((v - d) * 60)
    s = (v - d - m / 60) * 3600
    return d, m, s


def _abs_deg_min(v: float) -> tuple[int, float]:
    d = int(v)
    m = (v - d) * 60
    return d, m


def format_ddmmss(deg: float) -> str:
    d, m, s = _abs_deg_min_sec(abs(deg))
    return f"{d:d}°{m:02d}'{round(s):02d}\""


def format_ddmmmm(deg: float) -> str:
    d, m = _abs_deg_min(abs(deg))
    return f"{d:d}°{m:05.2f}'"


def format_angle(deg: float, fmt: str = "dms") -> str:
    if fmt == "dmm":
        return format_ddmmmm(deg)
    return format_ddmmss(deg)


def body_label(name: str) -> str:
    if name in ("Sun", "Moon"):
        return name
    if name in PLANET_BODIES:
        return name
    idx = NAVPAC_STAR_INDEX.get(name)
    if idx is not None:
        return f"{name} ({idx})"
    return name


def format_azimuth(deg: float) -> str:
    return f"{deg:.1f}°"


def format_position(lat: float, lon: float, fmt: str = "dms") -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    lat_s = format_angle(lat, fmt)
    lon_s = format_angle(lon, fmt)
    return f"{lat_s} {ns}, {lon_s} {ew}"
