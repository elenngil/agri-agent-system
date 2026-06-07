from models.shared_state import SharedState

def predict_future_water_stress(state: SharedState) -> str:

    cf  = state.climate_features
    wd  = state.weather_data
    sm  = state.soil_multiplier

    if cf is None or wd is None or sm is None:
        return "Desconocido"

    score = 0
    adjusted_dha = cf.dha * sm

    if adjusted_dha > 4: score += 2
    elif adjusted_dha > 2: score += 1

    if cf.etc > 4: score += 2
    elif cf.etc > 2: score += 1

    if wd.precipitation < 2: score += 2
    elif wd.precipitation < 5: score += 1

    heat_level = cf.heat_stress.get("level") if cf.heat_stress else None
    if heat_level == "Alto": score += 2
    elif heat_level == "Moderado": score += 1

    if score >= 7: return "Alto"
    if score >= 4: return "Moderado"
    return "Bajo"


def predict_irrigation_need(state: SharedState) -> str | None:

    cf   = state.climate_features
    wd   = state.weather_data
    sm   = state.soil_multiplier
    pred = state.predictions

    if cf is None or wd is None or sm is None or pred is None:
        return None

    fws = pred.future_water_stress
    if fws is None or cf.dha is None or cf.etc is None or wd.precipitation is None:
        return None

    score = 0

    if fws == "Alto": score += 3
    elif fws == "Moderado": score += 2

    if cf.dha > 4: score += 2
    elif cf.dha > 2: score += 1

    if cf.etc > 4: score += 2
    elif cf.etc > 2: score += 1

    if wd.precipitation < 2: score += 2
    elif wd.precipitation < 5: score += 1

    if sm > 1: score += 1

    if score >= 8: return "Alta"
    if score >= 4: return "Media"
    return "Baja"