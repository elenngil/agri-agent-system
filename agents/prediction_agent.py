from models.shared_state import SharedState, Predictions
from tools.climate_predictions import predict_future_water_stress, predict_irrigation_need


class PredictionAgent:

    def run(self, state: SharedState) -> SharedState:
        state.predictions = Predictions(
            future_water_stress=predict_future_water_stress(state),
            irrigation_need=None,
        )

        state.predictions.irrigation_need = predict_irrigation_need(state)

        return state