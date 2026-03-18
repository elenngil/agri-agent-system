def create_shared_state(station: str, start_date: str, end_date: str) -> dict:
    return {
        # Inputs del usuario
        "station": station,
        "start_date": start_date,
        "end_date": end_date,

        # Observation Agent
        "weather_data": None,
        "soil_multiplier": None,
        "crop_data": None,

        # Validation Agent
        "validation_result": None,

        # Inference Agent
        "climate features": None,

        # Prediction Agent
        "prediction": None,
        "risk_prediction": None,

        # Planification Agent
        "options": None,
        "final_plan": None,

        # Explanation Agent
        "explanation": None

    }
    