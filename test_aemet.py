from tools.weather_api import aemet_get

# Inventario de estaciones (es un endpoint muy típico para probar)
endpoint = "valores/climatologicos/inventarioestaciones/todasestaciones"

data = aemet_get(endpoint)
print(type(data), len(data))
print(data[0])