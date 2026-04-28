from models.shared_state import SharedState, WeatherData, CropData
from tools.weather_data import get_climate_summary
from tools.soil_data import get_soil_multiplier
from tools.crop_data import get_crop_data


class ObservationAgent:
    """Recopila datos de clima, suelo y cultivo y los guarda en el shared state."""

    def run(self, shared_state: SharedState) -> SharedState:
        weather_raw = get_climate_summary(
            shared_state.station,
            shared_state.start_date,
            shared_state.end_date
        )
        crop_raw = get_crop_data(
            shared_state.station,
            shared_state.selected_variety)

        shared_state.weather_data = (
            WeatherData(
                temperature_max=weather_raw["temperature_max"],
                temperature_min=weather_raw["temperature_min"],
                temperature_mean=weather_raw["temperature_mean"],
                precipitation=weather_raw["precipitation"],
                humidity=weather_raw["humidity"],
                wind=weather_raw["wind"],
                pressure=weather_raw["pressure"],
                days_count=weather_raw["days_count"],
            )
            if weather_raw
            else None
        )

        shared_state.soil_multiplier = get_soil_multiplier(shared_state.station)

        shared_state.crop_data = (
            CropData(
                variety=crop_raw["variety"],
                color=crop_raw["color"],
                water_need=crop_raw["water_need"],
                frost_sensitivity=crop_raw["frost_sensitivity"],
                heat_sensitivity=crop_raw["heat_sensitivity"],
                humidity_sensitivity=crop_raw["humidity_sensitivity"],
                optimal_temp_min=crop_raw["optimal_temp_min"],
                optimal_temp_max=crop_raw["optimal_temp_max"],
                optimal_humidity_max=crop_raw["optimal_humidity_max"],
                optimal_precip_mm=crop_raw["optimal_precip_mm"],
            )
            if crop_raw
            else None
        )

        return shared_state