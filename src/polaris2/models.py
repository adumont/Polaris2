from datetime import datetime

from pydantic import BaseModel

from polaris2.utils.angles import format_position


class Position(BaseModel):
    lat: float
    lon: float

    def display(self, fmt: str = "dms") -> str:
        return format_position(self.lat, self.lon, fmt)

    def __str__(self) -> str:
        return self.display("dms")


class SextantReading(BaseModel):
    body_name: str
    hs: float  # sextant altitude (raw, above visible horizon, before corrections)
    ho: float  # observed altitude (corrected, above celestial horizon)
    utc: datetime
    real_altitude: float
    correction_total: float


class SightReduction(BaseModel):
    body_name: str
    ho: float
    hc: float
    intercept_nmi: float
    azimut_zn: float
    lat_dr: float
    lon_dr: float
    utc: datetime
    selected: bool = True


class Fix(BaseModel):
    lat: float
    lon: float
    error_nmi: float | None = None
    iterations: int = 0


class Scenario(BaseModel):
    real_position: Position
    estimated_position: Position
    dr_error_nmi: float
    utc: datetime
    he_ft: float
    sextant_readings: list[SextantReading] = []
    sight_reductions: list[SightReduction] = []
    fix: Fix | None = None
