from models.shared_state import SharedState, ClimateFeatures
from tools.climate_features import (
    calculate_etc,
    calculate_dha,
    calculate_frost_risk,
    calculate_heat_stress,
    calculate_mildiu_risk,
    strong_wind_risk,
)


class InferenceAgent:
    
    def run(self, state: SharedState) -> SharedState:
        if state.weather_data is None:
            raise ValueError("weather_data no disponible en SharedState")
        if state.crop_data is None:
            raise ValueError("crop_data no disponible en SharedState")

        state.climate_features = ClimateFeatures(
            etc=calculate_etc(state.weather_data, state.start_date),
            dha=calculate_dha(state.weather_data, state.start_date),
            frost_risk=calculate_frost_risk(state.weather_data, state.crop_data),
            heat_stress=calculate_heat_stress(state.weather_data, state.crop_data),
            mildiu_risk=calculate_mildiu_risk(state.weather_data),
            strong_wind_risk=strong_wind_risk(state.weather_data),
        )

        return state