from models.shared_state import WeatherData, CropData


def calculate_etc(weather_data: WeatherData) -> float:
    tmin = weather_data.temperature_min
    tmax = weather_data.temperature_max
    tmed = weather_data.temperature_mean
    days = weather_data.days_count

    if tmin is None or tmax is None or tmed is None:
        return 0.0

    kc = 0.7

    et0 = 0.0023 * (tmax - tmin) ** 0.5 * (tmed + 17.8)
    etc_daily = et0 * kc

    etc_total = etc_daily * days  

    return etc_total

def calculate_dha(weather_data: WeatherData) -> float:
    """
    Calcula el déficit hídrico aparente a partir de la ETc y la precipitación.
    """
    etc = calculate_etc(weather_data)
    precipitation = weather_data.precipitation

    dha = etc - precipitation
    return max(dha, 0)


def calculate_frost_risk(weather_data: WeatherData, crop_data: CropData) -> dict:
    tmin = weather_data.temperature_min
    optimal_tmin = crop_data.optimal_temp_min

    if tmin is None:
        return {
            "level": "Desconocido",
            "score": 0.0,
            "value": None,
            "threshold": 0.0,
        }

    # Riesgo meteorológico real de helada
    if tmin <= 0:
        level, score = "Alto", 0.9
        threshold = 0.0
    elif tmin <= 2:
        level, score = "Moderado", 0.5
        threshold = 2.0
    elif tmin <= 5:
        level, score = "Bajo", 0.2
        threshold = 5.0
    else:
        level, score = "Nulo", 0.0
        threshold = 5.0

    return {
        "level": level,
        "score": score,
        "value": tmin,
        "threshold": threshold,
    }


def calculate_mildiu_risk(weather_data: WeatherData) -> dict:
    """
    Evalúa el riesgo de mildiu a partir de humedad y precipitación.
    """
    humidity = weather_data.humidity
    precipitation = weather_data.precipitation

    if humidity is None:
        return {
            "level": "Desconocido",
            "score": 0.0,
            "value": None,
            "threshold": 85,
        }

    if humidity >= 85:
        level, score = "Alto", 0.9
    elif humidity > 60 and 10 <= precipitation <= 30:
        level, score = "Moderado", 0.5
    else:
        level, score = "Bajo", 0.2

    return {
        "level": level,
        "score": score,
        "value": humidity,
        "threshold": 85,
    }


def calculate_heat_stress(weather_data: WeatherData, crop_data: CropData) -> dict:
    """
    Evalúa el riesgo de estrés térmico para un cultivo.
    """
    tmax = weather_data.temperature_max
    optimal_temp_max = crop_data.optimal_temp_max

    if tmax <= optimal_temp_max:
        level, score = "Bajo", 0.2
    elif tmax <= optimal_temp_max + 3:
        level, score = "Moderado", 0.5
    else:
        level, score = "Alto", 0.9

    return {
        "level": level,
        "score": score,
        "value": tmax,
        "threshold": optimal_temp_max + 3,
    }


def strong_wind_risk(weather_data: WeatherData) -> dict:
    """
    Evalúa el riesgo de viento fuerte para el cultivo.
    """
    wind_speed = weather_data.wind

    if wind_speed is None:
        return {
            "level": "Desconocido",
            "score": 0.0,
            "value": None,
            "threshold": 50,
        }

    if wind_speed >= 50:
        level, score = "Alto", 0.9
    elif wind_speed >= 30:
        level, score = "Moderado", 0.5
    else:
        level, score = "Bajo", 0.2

    return {
        "level": level,
        "score": score,
        "value": wind_speed,
        "threshold": 50,
    }