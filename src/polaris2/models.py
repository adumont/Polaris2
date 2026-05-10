from datetime import datetime

from pydantic import BaseModel


class Position(BaseModel):
    lat: float
    lon: float

    def __str__(self) -> str:
        ns = "N" if self.lat >= 0 else "S"
        ew = "E" if self.lon >= 0 else "W"
        return f"{abs(self.lat):.4f}°{ns}  {abs(self.lon):.4f}°{ew}"


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
