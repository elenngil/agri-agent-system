from tools.climate_features import calculate_dha, calculate_frost_risk, calculate_heat_stress, calculate_mildiu_risk, strong_wind_risk, calculate_etc

class InferenceAgent:

    def run(self, shared_state: dict) -> dict:
        weather = shared_state["weather_data"]
        crop = shared_state["crop_data"]

        features = {
            "etc": calculate_etc(weather),
            "dha": calculate_dha(weather),
            "frost_risk": calculate_frost_risk(weather, crop),
            "heat_stress": calculate_heat_stress(weather, crop),
            "mildiu_risk": calculate_mildiu_risk(weather),
            "strong_wind_risk": strong_wind_risk(weather)
        }

        shared_state["climate_features"] = features
        return shared_state
