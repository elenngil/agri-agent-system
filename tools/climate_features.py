from datetime import datetime
from models.shared_state import WeatherData, CropData


def get_kc(month: int) -> float:
    """
    La funcioón calcula el coeficiente del cultivo base (Kc), es decir, cuánta agua necesita el cultivo según la fase fenológica.
    Se aproximan los valores a los encontrados en el documento oficial de la FAO 56, ajústandolos a las condiciones climaticas de España.
    """

    if month in [12, 1, 2]: # Reposo vegetativo: vid dormida, no hay hojas ni crecimiento activo
        return 0.30

    elif month in [3, 4]: # Brotación: comienzan a salir las hojas
        return 0.45

    elif month in [5, 6]: # Crecimiento vegetativo / floración: los brotes se desarrollan, las hojas crecen y se forman las flores
        return 0.75

    elif month in [7, 8]: # Envero y maduración: momento en el que las uvas cambian de color, se llenan y maduran
        return 0.65

    elif month == 9: # Vendimia: recolección de las uvas, el crecimiento se detiene y el consumo de agua disminuye
        return 0.55

    else:  # 10, 11 Senescencia: las hojas amarillean y caen, el crecimiento se detiene y el consumo de agua es mínimo
        return 0.40


def calculate_etc(weather_data: WeatherData, start_date: datetime) -> float:
    """
    La función calcula la evapotranspiración del cultivo (ETc) a partir de los datos climáticos.
    Para ello, se utiliza la fórmula simplificada de Hargreaves-Samani.
    """

    tmin = weather_data.temperature_min
    tmax = weather_data.temperature_max
    tmed = weather_data.temperature_mean
    days = weather_data.days_count

    if tmin is None or tmax is None or tmed is None or days is None:
        return 0.0
    if tmax < tmin:
        return 0.0

    kc = get_kc(start_date.month)

    # Fórmula de Hargreaves-Samani simplificada
    et0 = 0.0023 * (tmax - tmin) ** 0.5 * (tmed + 17.8)

    etc_daily = et0 * kc
    etc_total = etc_daily * days # demanda a lo largo del periodo pedido por el usuario

    return round(etc_total, 2)

def calculate_dha(weather_data: WeatherData, start_date: datetime) -> float:
    """
    La función calcula el deficit hídrico acumulado (dha) que es la diferencia entre lo que la vid necesita y lo que ha recibido de la lluvia.
    """
    etc = calculate_etc(weather_data, start_date)
    precipitation = weather_data.precipitation

    dha = etc - precipitation
    return max(dha, 0)


def calculate_frost_risk(weather_data: WeatherData, crop_data: CropData) -> dict:
    """
    La función calcula el riesgo de helada para un cultivo específico.
    Para ello se tiene en cuenta la diferencia entre la temperatura mínima registrada y la temperatura mínima óptima para esa variedad de vid.

    Devuelve un diccionario con:
    - level: clasificación del riesgo (Nulo, Bajo, Moderado o Alto)
    - score: puntuación numéricadel riesgo 
    - value: valor de la temperatura mínima registrada
    - threshold: la línea que no debería cruzarse (en este caso, la temperatura mínima óptima para el cultivo)
    """

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