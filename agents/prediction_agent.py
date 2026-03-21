from tools.climate_predictions import predict_irrigation_need, predict_future_water_stress

class PredictionAgent:

    def run(self, shared_state: dict) -> dict:
        weather = shared_state["weather_data"]
        crop = shared_state["crop_data"]

        shared_state["prediction"] = {
            "future_water_stress": predict_future_water_stress(shared_state),
            "irrigation_need": predict_irrigation_need(shared_state)
        }

        return shared_state
