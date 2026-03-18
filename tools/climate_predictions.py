from tools.weather_data import get_climate_summary

def predict_future_water_stress(shared_state: dict) -> str:
    climate_features = shared_state["climate_features"]
    weather_data = shared_state["weather_data"]
    soil_multiplier = shared_state["soil_multiplier"]

    dha = climate_features["dha"]
    etc = climate_features["etc"]
    heat_stress = climate_features["heat_stress"]
    precipitation = weather_data.get("precipitation")

    adjusted_dha = dha * soil_multiplier

    fws = 0

    if adjusted_dha > 4: # Umbral de horas de riego necesarias
        fws += 2
    elif adjusted_dha > 2:
        fws += 1

    if etc > 4: # Umbral de evapotranspiración (pérdida de agua)
        fws += 2
    elif etc > 2:
        fws += 1

    if precipitation < 2: # Precipitación
        fws += 2
    elif precipitation < 5:
        fws += 1

    if heat_stress == "Alto": # Calor
        fws += 2
    elif heat_stress == "Moderado":
        fws += 1


    if fws >= 7:
        return "Alto"
    elif fws >= 4:
        return "Moderado"
    else:
        return "Bajo"
    
test_shared_state = {
    "weather_data": {
        "precipitation": 1.0
    },
    "soil_multiplier": 0.8,
    "climate_features": {
        "dha": 4.5,
        "etc": 4.2,
        "heat_stress": "Moderado"
    }
}

#print(predict_future_water_stress(test_shared_state))

def predict_irrigation_need(shared_state: dict) -> str | None:
    prediction = shared_state.get("prediction")
    climate_features = shared_state.get("climate_features")
    weather_data = shared_state.get("weather_data")
    soil_multiplier = shared_state.get("soil_multiplier")

    if prediction is None or climate_features is None or weather_data is None or soil_multiplier is None:
        return None

    future_water_stress = prediction.get("future_water_stress")
    dha = climate_features.get("dha")
    etc = climate_features.get("etc")
    precipitation = weather_data.get("precipitation")

    if future_water_stress is None or dha is None or etc is None or precipitation is None:
        return None

    score = 0

    # 1. Estrés hídrico futuro
    if future_water_stress == "Alto":
        score += 3
    elif future_water_stress == "Moderado":
        score += 2
    else:
        score += 0

    # 2. Déficit hídrico actual
    if dha > 4:
        score += 2
    elif dha > 2:
        score += 1

    # 3. Evapotranspiración alta
    if etc > 4:
        score += 2
    elif etc > 2:
        score += 1

    # 4. Poca lluvia
    if precipitation < 2:
        score += 2
    elif precipitation < 5:
        score += 1

    # 5. Suelo con baja retención
    if soil_multiplier > 1:
        score += 1

    if score >= 8:
        return "Alta"
    elif score >= 4:
        return "Media"
    else:
        return "Baja"
    
#print(predict_irrigation_need(test_shared_state))