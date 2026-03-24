from datetime import date
from tools.weather_data import get_climate_summary

weather_data = get_climate_summary("B013X", date(2024, 1, 21), date(2024, 1, 31))
print(weather_data)