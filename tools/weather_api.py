import os
import requests
from dotenv import load_dotenv

load_dotenv()  # Lee el archivo .env

BASE = "https://opendata.aemet.es/opendata/api"

def aemet_get(endpoint: str, params: dict | None = None, timeout: int = 30):
    """
    Llama a AEMET (paso 1) y luego descarga los datos reales (paso 2).
    endpoint ejemplo:
      'valores/climatologicos/inventarioestaciones/todasestaciones'
    """
    api_key = os.getenv("AEMET_API_KEY")
    if not api_key:
        raise RuntimeError("No encuentro AEMET_API_KEY. Revisa tu archivo .env")

    params = dict(params or {})
    params["api_key"] = api_key

    # PASO 1: pedir a AEMET la URL donde están los datos
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=timeout)
    r.raise_for_status()
    meta = r.json()

    if meta.get("estado") != 200:
        raise RuntimeError(f"AEMET devolvió error: {meta}")

    datos_url = meta["datos"]

    # PASO 2: descargar los datos reales
    r2 = requests.get(datos_url, timeout=timeout)
    r2.raise_for_status()
    return r2.json()