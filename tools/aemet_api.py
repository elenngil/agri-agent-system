import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE = "https://opendata.aemet.es/opendata/api"

def aemet_get(endpoint: str, params: dict | None = None, timeout: int = 30):
    """
    Llama a AEMET (paso 1) y luego descarga los datos reales (paso 2).
    Devuelve:
      - dict/list si es JSON
      - str si es texto/CSV
    """
    api_key = os.getenv("AEMET_API_KEY")
    if not api_key:
        raise RuntimeError("No encuentro AEMET_API_KEY. Revisa tu archivo .env")

    params = dict(params or {})
    params["api_key"] = api_key

    # PASO 1
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=timeout)
    r.raise_for_status()
    meta = r.json()

    if meta.get("estado") != 200:
        raise RuntimeError(f"AEMET devolvió error: {meta}")

    datos_url = meta["datos"]

    # PASO 2
    r2 = requests.get(datos_url, timeout=timeout)
    r2.raise_for_status()

    ctype = (r2.headers.get("Content-Type") or "").lower()
    if "application/json" in ctype:
        return r2.json()
    return r2.json()  

class AemetError(Exception):
    """Error específico de AEMET."""
    pass
def aemet_get(endpoint: str, params: dict | None = None, timeout: int = 30):
    api_key = os.getenv("AEMET_API_KEY")
    if not api_key:
        raise AemetError("AEMET_API_KEY no configurada en .env")
    params = dict(params or {})
    params["api_key"] = api_key
    try:
        r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=timeout)
        r.raise_for_status()
    except requests.exceptions.Timeout:
        raise AemetError(f"Timeout al conectar con AEMET: {endpoint}")
    except requests.exceptions.RequestException as e:
        raise AemetError(f"Error de conexión con AEMET: {e}")
    meta = r.json()
    
    if meta.get("estado") != 200:
        raise AemetError(f"AEMET respondió con error: {meta.get('descripcion', meta)}")
    datos_url = meta.get("datos")
    if not datos_url:
        raise AemetError("Respuesta de AEMET sin URL de datos")
    try:
        r2 = requests.get(datos_url, timeout=timeout)
        r2.raise_for_status()
        return r2.json()
    except Exception as e:
        raise AemetError(f"Error descargando datos de AEMET: {e}")