from dataclasses import dataclass, field
@dataclass
class IrrigationPlan:
    base_liters: float
    adjusted_liters: float
    adjustment_reason: str
    soil_multiplier: float
    assumed_values: list[str] = field(default_factory=list)
@dataclass
class ClimateSummary:
    condition: str          # "óptimo", "estrés térmico", "frío", "húmedo", etc.
    temp_min: float
    temp_max: float
    precipitation: float
    humidity: float
    interpretation: str
@dataclass
class CropStatus:
    phase: str              # "brotación", "crecimiento", "maduración", "reposo"
    recommendation: str
    assumed: bool = False   # True si la fase se estimó sin datos reales
@dataclass
class PreventionItem:
    risk: str
    label: str
    priority: str           # "alta", "media", "baja"
    action: str
@dataclass
class DailyPlan:
    irrigation: IrrigationPlan
    climate: ClimateSummary
    crop_status: CropStatus
    prevention: list[PreventionItem]
    explanation: str
    sms: str