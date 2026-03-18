from .weather_api import aemet_get
from datetime import date

def get_climate_summary(station: str, start_date: date, end_date: date):
    start = start_date.strftime("%Y-%m-%dT00:00:00UTC")
    end = end_date.strftime("%Y-%m-%dT23:59:59UTC")

    endpoint = f"valores/climatologicos/diarios/datos/fechaini/{start}/fechafin/{end}/estacion/{station}"
    data = aemet_get(endpoint)

    return data

#test_temps = get_climate_summary(station = "3195", start_date = date(2025,5,13), end_date = date(2025,5,13))




