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
    ho: float
    utc: datetime
    real_altitude: float
    correction_total: float


class SightReduction(BaseModel):
    body_name: str
    ho: float
    hc: float
    alpha_nmi: float
    azimut_zn: float
    lat_dr: float
    lon_dr: float
    utc: datetime


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
