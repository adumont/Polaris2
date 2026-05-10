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


def parse_angle(value: float) -> float:
    v = abs(value)
    d = int(v // 10000)
    rest = v - d * 10000
    if rest > 100.0:  # noqa: PLR2004
        return ddmmss_to_deg(value)
    else:
        return ddmmmm_to_deg(value)
