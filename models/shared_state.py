from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class WeatherData:
    temperature_max: float
    temperature_min: float
    temperature_mean: float
    precipitation: float
    humidity: Optional[float]
    wind: Optional[float]
    pressure: Optional[float]
    days_count: int


@dataclass
class CropData:
    variety: str
    color: str
    water_need: str
    frost_sensitivity: str
    heat_tolerance: str
    humidity_sensitivity: str
    optimal_temp_min: float
    optimal_temp_max: float
    optimal_humidity_max: float
    optimal_precip_mm: float


@dataclass
class ClimateFeatures:
    etc: float
    dha: float
    frost_risk: str
    heat_stress: str
    mildiu_risk: str
    strong_wind_risk: str


@dataclass
class Predictions:
    future_water_stress: str
    irrigation_need: str


@dataclass
class SharedState:
    station: str
    start_date: date
    end_date: date
    ccaa: str = ""

    weather_data: Optional[WeatherData] = None
    soil_multiplier: Optional[float] = None
    crop_data: Optional[CropData] = None

    climate_features: Optional[ClimateFeatures] = None
    predictions: Optional[Predictions] = None

    alerts: list = field(default_factory=list)
    scenarios: list = field(default_factory=list)
    explanation: Optional[dict] = None