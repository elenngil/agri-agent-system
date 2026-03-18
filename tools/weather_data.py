from tools.aemet_api import aemet_get
from datetime import date
from smolagents import tool

def to_float(x):
    if x is None:
        return None
    elif isinstance(x, (int, float)):
        return float(x)
    elif isinstance(x, str):
        x = x.replace(",", ".") 
        return float(x)

@tool
def get_climate_summary(station: str, start_date: date, end_date: date) -> dict:

    '''
    Obtiene un resumen de las condiciones climáticas para una estación y un rango de fechas dado.
    Args:
        station (str): El ID de la estación meteorológica.
        start_date (date): La fecha de inicio del rango.
        end_date (date): La fecha de fin del rango.
    Returns:
        dict: diccionario con las condiciones climáticas resumidas, incluyendo temperatura máxima, media y mínima, precipitación, humedad, viento y presión.
    '''

    start = start_date.strftime("%Y-%m-%dT00:00:00UTC")
    end = end_date.strftime("%Y-%m-%dT23:59:59UTC")

    endpoint = f"valores/climatologicos/diarios/datos/fechaini/{start}/fechafin/{end}/estacion/{station}"
    data = aemet_get(endpoint)

    d = data[0]

    tmin = to_float(d.get("tmin"))
    tmax = to_float(d.get("tmax"))
    tmed = to_float(d.get("tmed"))
    prec = to_float(d.get("prec")) or 0.0
    hr   = to_float(d.get("hrMedia"))
    wind = to_float(d.get("velmedia"))
    pmax = to_float(d.get("presMax"))
    pmin = to_float(d.get("presMin"))

    if pmax is not None and pmin is not None:
        pressure = (pmax + pmin) / 2
    else: pressure = 0.0

    summary = {'temperature_max': tmax, 
                'temperature_mean': tmed, 
                'temperature_min': tmin, 
                'precipitation': prec, 
                'humidity': hr,
                'wind': wind,
                'pressure': pressure
                }
    
    return summary





