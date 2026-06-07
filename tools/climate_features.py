from datetime import datetime
from models.shared_state import WeatherData, CropData

# Indicadores agronómicos (consumidos por el DeliberativeAgent)

def get_kc(month: int) -> float:

    if month in [12, 1, 2]:
        return 0.30

    elif month in [3, 4]: 
        return 0.45

    elif month in [5, 6]: 
        return 0.75

    elif month in [7, 8]: 
        return 0.65

    elif month == 9: 
        return 0.55

    else: 
        return 0.40


def calculate_etc(weather_data: WeatherData, start_date: datetime) -> float:


    tmin = weather_data.temperature_min
    tmax = weather_data.temperature_max
    tmed = weather_data.temperature_mean
    days = weather_data.days_count

    if tmin is None or tmax is None or tmed is None or days is None:
        return 0.0
    if tmax < tmin:
        return 0.0

    kc = get_kc(start_date.month)

    et0 = 0.0023 * (tmax - tmin) ** 0.5 * (tmed + 17.8)

    etc_daily = et0 * kc
    etc_total = etc_daily * days

    return round(etc_total, 2)

def calculate_dha(weather_data: WeatherData, start_date: datetime) -> float:

    etc = calculate_etc(weather_data, start_date)
    precipitation = weather_data.precipitation

    dha = etc - precipitation
    return max(dha, 0)

# Indicadores de riesgo (consumidos por el RiskAgent)

def calculate_frost_risk(weather_data: WeatherData, crop_data: CropData) -> dict:

    tmin = weather_data.temperature_min
    optimal_tmin = crop_data.optimal_temp_min

    if tmin is None:
        return {"level": "Desconocido", "score": 0.0, "value": None, "threshold": 0.0} 

    desviacion = optimal_tmin - tmin

    if tmin <= 0:
        level, score = "Alto", 0.9       
        threshold = 0.0
    elif desviacion >= 8:
        level, score = "Alto", 0.8        
        threshold = optimal_tmin - 8
    elif desviacion >= 5:
        level, score = "Moderado", 0.5   
        threshold = optimal_tmin - 5
    elif desviacion >= 2:
        level, score = "Bajo", 0.2        
        threshold = optimal_tmin - 2
    else:
        level, score = "Nulo", 0.0        
        threshold = optimal_tmin

    return {
        "level": level,
        "score": score,
        "value": tmin,
        "threshold": threshold,
    }


def calculate_mildiu_risk(weather_data: WeatherData) -> dict:

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
    
    tmax = weather_data.temperature_max
    optimal_temp_max = crop_data.optimal_temp_max

    if tmax is None:
        return {
            "level": "Desconocido",
            "score": 0.0,
            "value": None,
            "threshold": optimal_temp_max,
        }

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