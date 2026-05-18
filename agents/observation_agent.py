from models.shared_state import SharedState, WeatherData, CropData
from tools.weather_data import get_climate_summary
from tools.soil_data import get_soil_multiplier, get_soil_from_ccaa
from tools.crop_data import get_crop_data, get_variety_from_ccaa


class ObservationAgent:
    """Recopila datos de clima, suelo y cultivo y los guarda en el SharedState."""

    def run(self, state: SharedState) -> SharedState:

        # ── Datos meteorológicos ──────────────────────────────────────────────
        weather_raw = get_climate_summary(state.station, state.start_date, state.end_date)

        state.weather_data = (
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
            if weather_raw else None
        )

        soil_type = getattr(state, "soil_type", None)
        if soil_type:
            state.soil_multiplier = get_soil_multiplier(soil_type)
        else:
            soil = get_soil_from_ccaa(state.station)
            state.soil_multiplier = get_soil_multiplier(soil)

        variety = getattr(state, "selected_variety", None)
        if not variety:
            variety = get_variety_from_ccaa(state.station)

        crop_raw = get_crop_data(variety)

        state.crop_data = (
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
            if crop_raw else None
        )

        return state