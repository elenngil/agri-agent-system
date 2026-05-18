from models.shared_state import SharedState, Predictions
from tools.climate_predictions import predict_future_water_stress, predict_irrigation_need


class PredictionAgent:

    def run(self, state: SharedState) -> SharedState:
        future_water_stress = predict_future_water_stress(state)

        state.predictions = Predictions(
            future_water_stress=future_water_stress,
            irrigation_need=None,
        )

        state.predictions.irrigation_need = predict_irrigation_need(state)

        return state