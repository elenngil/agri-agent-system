from tools.weather_api import aemet_get
from tools.aemet_climate import get_temperatures

if __name__ == "__main__":
    data = aemet_get("valores/climatologicos/inventarioestaciones/todasestaciones")

    # suele ser una lista de estaciones (dicts)
    print(type(data))
    print("n =", len(data) if hasattr(data, "__len__") else "¿?")
    print("primera fila:", data[0] if isinstance(data, list) and data else data[:200])

