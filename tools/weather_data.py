from datetime import date
from smolagents import tool
from tools.aemet_api import aemet_get


def to_float(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        x = x.replace(",", ".").strip()
        try:
            return float(x)
        except ValueError:
            return None
    return None


@tool
def get_climate_summary(station: str, start_date: date, end_date: date) -> dict:
    """
    Obtiene un resumen climático para una estación meteorológica en un rango de fechas.

    Args:
        station: ID de la estación meteorológica.
        start_date: Fecha inicial del rango.
        end_date: Fecha final del rango.

    Returns:
        Un diccionario con temperatura máxima, mínima y media, precipitación acumulada,
        humedad media, viento máximo y presión, o None si no hay datos disponibles.
    """
    start = start_date.strftime("%Y-%m-%dT00:00:00UTC")
    end = end_date.strftime("%Y-%m-%dT23:59:59UTC")

    endpoint = (
        f"valores/climatologicos/diarios/datos/"
        f"fechaini/{start}/fechafin/{end}/estacion/{station}"
    )
    data = aemet_get(endpoint)

    if not data:
        return None

    tmins = [to_float(d.get("tmin")) for d in data if d.get("tmin")]
    tmaxs = [to_float(d.get("tmax")) for d in data if d.get("tmax")]
    tmeds = [to_float(d.get("tmed")) for d in data if d.get("tmed")]
    precs = [(to_float(d.get("prec")) or 0.0) for d in data]
    hrs = [to_float(d.get("hrMedia")) for d in data if d.get("hrMedia")]
    winds = [to_float(d.get("velmedia")) for d in data if d.get("velmedia")]
    pressures = [to_float(d.get("presMax")) for d in data if d.get("presMax")]

    summary = {
        "temperature_max": max(tmaxs) if tmaxs else None,
        "temperature_min": min(tmins) if tmins else None,
        "temperature_mean": sum(tmeds) / len(tmeds) if tmeds else None,
        "precipitation": sum(precs),
        "humidity": sum(hrs) / len(hrs) if hrs else None,
        "wind": max(winds) if winds else None,
        "pressure": sum(pressures) / len(pressures) if pressures else None,
        "days_count": len(data),
    }

    return summary