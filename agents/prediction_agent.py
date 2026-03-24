from models.shared_state import SharedState, Predictions
from tools.climate_predictions import predict_irrigation_need, predict_future_water_stress


class PredictionAgent:
    def run(self, shared_state: SharedState) -> SharedState:
        future_water_stress = predict_future_water_stress(shared_state)

        shared_state.predictions = Predictions(
            future_water_stress=future_water_stress,
            irrigation_need=""
        )

        irrigation_need = predict_irrigation_need(shared_state)

        shared_state.predictions.irrigation_need = irrigation_need
        return shared_state