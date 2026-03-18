test_data = {
    "temperature_min": 15.0,
    "temperature_max": 30.0,
    "temperature_mean": 22.5,
    "precipitation": 5.0,
    "wind": 20.0
}

crop_td = {
    "optimal_temp_min": 18.0,
    "optimal_temp_max": 28.0
}

def calculate_etc(weather_data: dict) -> float:
    '''
    Calcula la evapotranspiración (ETc) para un cultivo específico utilizando datos climáticos y características del cultivo.
    Args:
        weather_data (dict): Un diccionario que contiene datos climáticos relevantes, como temperatura, humedad, velocidad del viento, etc.
        crop_data (dict): Un diccionario que contiene información sobre el cultivo, como su coeficiente de cultivo (Kc), etc.
    '''
    tmin = weather_data.get("temperature_min")
    tmax = weather_data.get("temperature_max")
    tmed = weather_data.get("temperature_mean")
    kc = 0.7  # Coeficiente de cultivo para la fase media del cultivo (se podría hacer por fase fenológica)

    et0 = 0.0023 * (tmax - tmin)**0.5 * (tmed + 17.8)  # Fórmula de Hargreaves para calcular ET0
    etc = et0 * kc  # ETc = ET0 * Kc
    return etc

#print(calculate_etc(test_data))

def calculate_dha(weather_data: dict) -> float:
    '''
    Calcula las horas de riego necesarias para un cultivo específico utilizando datos climáticos.
    Args:
        weather_data (dict): Un diccionario que contiene datos climáticos relevantes.
    '''
    etc = calculate_etc(weather_data)
    precipitation = weather_data.get("precipitation")

    dha = etc - precipitation  # Horas de riego necesarias = ETc - precipitación
    return max(dha, 0) 

#print(calculate_dha(test_data))

def calculate_frost_risk(weather_data: dict, crop_data: dict) -> str:
    '''
    Evalúa el riesgo de heladas para un cultivo específico utilizando datos climáticos.
    Args:
        weather_data (dict): Un diccionario que contiene datos climáticos relevantes.
        crop_data (dict): Un diccionario que contiene información sobre el cultivo.
    Returns:
        str: Una evaluación del riesgo de heladas ("Alto", "Moderado", "Bajo").
    '''
    tmin = weather_data.get("temperature_min")
    optimal_tmin = crop_data.get("optimal_temp_min")

    if tmin < optimal_tmin:
        return "Alto"
    elif tmin <= optimal_tmin + 3:
        return "Moderado"
    else:
        return "Bajo"
    
def calculate_mildiu_risk(weather_data: dict) -> str:
    '''
    Evalúa el riesgo de mildiu para un cultivo específico utilizando datos climáticos.
    Args:
        weather_data (dict): Un diccionario que contiene datos climáticos relevantes.
    Returns:
        str: Una evaluación del riesgo de mildiu ("Alto", "Moderado", "Bajo").
    '''
    humidity = weather_data.get("humidity")
    precipitation = weather_data.get("precipitation")

    if humidity >= 85:
        return "Alto"
    elif humidity > 60 and 10 <= precipitation <= 30:
        return "Moderado"
    else:
        return "Bajo"

def calculate_heat_stress(weather_data: dict, crop_data: dict) -> str:
    '''
    Evalúa el riesgo de estrés térmico para un cultivo específico utilizando datos climáticos.
    Args:
        weather_data (dict): Un diccionario que contiene datos climáticos relevantes.
        crop_data (dict): Un diccionario que contiene información sobre el cultivo.
    Returns:
        str: Una evaluación del riesgo de estrés térmico ("Alto", "Moderado", "Bajo").
    '''
    tmax = weather_data.get("temperature_max")
    optimal_temp_max = crop_data.get("optimal_temp_max")

    if tmax <= optimal_temp_max:
        heat_stress = "Bajo"
    elif tmax <= optimal_temp_max + 3:
        heat_stress = "Moderado"
    else:
        heat_stress = "Alto"

    return heat_stress

#print(calculate_heat_stress(test_data, crop_td))

def strong_wind_risk(weather_data: dict) -> str:
    '''
    Evalúa el riesgo de viento fuerte para un cultivo específico utilizando datos climáticos.
    Args:
        weather_data (dict): Un diccionario que contiene datos climáticos relevantes.
    Returns:
        str: Una evaluación del riesgo de viento fuerte ("Alto", "Moderado", "Bajo").
    '''
    wind_speed = weather_data.get("wind")

    if wind_speed >= 50:
        return "Alto"
    elif wind_speed >= 30:
        return "Moderado"
    else:
        return "Bajo"
    
