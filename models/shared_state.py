from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List
from enum import Enum


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
    heat_sensitivity: str
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

class RiskLevel(Enum):
    LOW = "bajo"
    MEDIUM = "medio"
    HIGH = "alto"
    CRITICAL = "crítico"

@dataclass
class Alert:
    risk_type: str
    level: RiskLevel
    value: float | str | None
    threshold: float | str | None
    penalty: float
    ccaa: str
    valid_until: str
    message: str

@dataclass
class Action:
    type: str
    intensity: str
    cost: float


@dataclass
class Scenario:
    actions: list[Action]
    utility: float
    breakdown: dict


@dataclass
class IrrigationPlan:
    base_liters: float
    adjusted_liters: float
    adjustment_reason: str
    soil_multiplier: float
    assumed_values: bool

@dataclass
class ClimateSummary:
    condition: str
    temp_min: float
    temp_max: float
    precipitation: float
    humidity: float
    interpretation: str

@dataclass
class CropStatus:
    phase: str
    recommendation: str
    assumed: bool

@dataclass
class PreventionItem:
    risk: str
    label: str
    priority: str
    action: str

@dataclass
class DailyPlan:
    irrigation: IrrigationPlan
    climate: ClimateSummary
    crop_status: CropStatus
    prevention: list[PreventionItem]
    explanation: str
    sms: str


@dataclass
class SharedState:
    station: str
    start_date: date
    end_date: date
    ccaa: str = ""

    selected_variety: Optional[str] = None

    weather_data: Optional[WeatherData] = None
    soil_multiplier: Optional[float] = None
    crop_data: Optional[CropData] = None

    climate_features: Optional[ClimateFeatures] = None
    predictions: Optional[Predictions] = None

    alerts: list[Alert] = field(default_factory=list)
    scenarios: list[Scenario] = field(default_factory=list)
    explanation: Optional[dict] = None

    daily_plan: Optional[DailyPlan] = None



