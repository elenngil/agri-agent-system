def predict_future_water_stress(shared_state) -> str:
    climate_features = shared_state.climate_features
    weather_data = shared_state.weather_data
    soil_multiplier = shared_state.soil_multiplier

    if climate_features is None or weather_data is None or soil_multiplier is None:
        return "Desconocido"

    dha = climate_features.dha
    etc = climate_features.etc
    heat_stress = climate_features.heat_stress
    precipitation = weather_data.precipitation

    adjusted_dha = dha * soil_multiplier

    fws = 0

    if adjusted_dha > 4:
        fws += 2
    elif adjusted_dha > 2:
        fws += 1

    if etc > 4:
        fws += 2
    elif etc > 2:
        fws += 1

    if precipitation < 2:
        fws += 2
    elif precipitation < 5:
        fws += 1

    heat_level = heat_stress["level"] if heat_stress else None
    if heat_level == "Alto":
        fws += 2
    elif heat_level == "Moderado":
        fws += 1

    if fws >= 7:
        return "Alto"
    elif fws >= 4:
        return "Moderado"
    else:
        return "Bajo"


def predict_irrigation_need(shared_state) -> str | None:
    predictions = shared_state.predictions
    climate_features = shared_state.climate_features
    weather_data = shared_state.weather_data
    soil_multiplier = shared_state.soil_multiplier

    if (
        predictions is None
        or climate_features is None
        or weather_data is None
        or soil_multiplier is None
    ):
        return None

    future_water_stress = predictions.future_water_stress
    dha = climate_features.dha
    etc = climate_features.etc
    precipitation = weather_data.precipitation

    if future_water_stress is None or dha is None or etc is None or precipitation is None:
        return None

    score = 0

    if future_water_stress == "Alto":
        score += 3
    elif future_water_stress == "Moderado":
        score += 2

    if dha > 4:
        score += 2
    elif dha > 2:
        score += 1

    if etc > 4:
        score += 2
    elif etc > 2:
        score += 1

    if precipitation < 2:
        score += 2
    elif precipitation < 5:
        score += 1

    if soil_multiplier > 1:
        score += 1

    if score >= 8:
        return "Alta"
    elif score >= 4:
        return "Media"
    else:
        return "Baja"