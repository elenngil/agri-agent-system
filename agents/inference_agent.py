from models.shared_state import SharedState, ClimateFeatures
from tools.climate_features import (
    calculate_dha,
    calculate_frost_risk,
    calculate_heat_stress,
    calculate_mildiu_risk,
    strong_wind_risk,
    calculate_etc,
)


class InferenceAgent:

    def run(self, shared_state: SharedState) -> SharedState:
        weather = shared_state.weather_data
        crop = shared_state.crop_data

        if weather is None:
            raise ValueError("weather_data no está disponible en shared_state")
        if crop is None:
            raise ValueError("crop_data no está disponible en shared_state")

        shared_state.climate_features = ClimateFeatures(
            etc=calculate_etc(weather, shared_state.start_date),
            dha=calculate_dha(weather, shared_state.start_date),
            frost_risk=calculate_frost_risk(weather, crop),
            heat_stress=calculate_heat_stress(weather, crop),
            mildiu_risk=calculate_mildiu_risk(weather),
            strong_wind_risk=strong_wind_risk(weather),
        )

        return shared_state