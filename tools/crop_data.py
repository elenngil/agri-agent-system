import pandas as pd
from tools.aemet_stations import station_to_ccaa


def get_crop_data(station: str, variety: str | None = None) -> dict:
    """
    Obtiene información del cultivo asociado a una estación meteorológica
    o a una variedad específica si se proporciona.

    Args:
        station: ID de la estación meteorológica.
        variety: Variedad seleccionada por el usuario (opcional).

    Returns:
        Diccionario con características agronómicas del cultivo.
    """

    crop_df = pd.read_csv("data/grape_profiles.csv", index_col="grape_variety")

    # ✅ 1. Si el usuario ha elegido variedad → usarla
    if variety:
        variety_clean = variety.strip().lower()

        # buscar sin sensibilidad a mayúsculas
        matches = [
            v for v in crop_df.index
            if v.lower() == variety_clean
        ]

        if not matches:
            raise ValueError(f"No existe la variedad '{variety}' en el dataset")

        crop_type = matches[0]

    # ✅ 2. Si no hay variedad → fallback por estación → CCAA
    else:
        crops = pd.read_csv("data/ccaa_grape.csv", index_col="ccaa")["grape"].to_dict()
        ccaa = station_to_ccaa(station)

        crop_type = crops.get(ccaa)

        if crop_type is None:
            raise ValueError(f"No hay cultivo asociado a la CCAA de la estación {station}")

    # ✅ 3. Obtener fila del cultivo
    if crop_type not in crop_df.index:
        raise ValueError(
            f"No encuentro información sobre el cultivo '{crop_type}'"
        )

    row = crop_df.loc[crop_type]

    return {
        "variety": crop_type,
        "color": row["color"],
        "water_need": row["water_need"],
        "frost_sensitivity": row["frost_sensitivity"],
        "heat_sensitivity": row["heat_sensitivity"],
        "humidity_sensitivity": row["humidity_sensitivity"],
        "optimal_temp_min": float(row["optimal_temp_min"]),
        "optimal_temp_max": float(row["optimal_temp_max"]),
        "optimal_humidity_max": float(row["optimal_humidity_max"]),
        "optimal_precip_mm": float(row["optimal_precip_mm"]),
    }