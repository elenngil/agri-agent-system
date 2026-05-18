import pandas as pd
from tools.aemet_stations import station_to_ccaa


def get_variety_from_ccaa(station: str) -> str:

    """
    Devuelve la variedad predominante de la región asociada a la estación meteorológica en el caso de que el usuario no la especifique (valor por defecto).
    """

    ccaa  = station_to_ccaa(station)
    crops = pd.read_csv("data/ccaa_grape.csv", index_col="ccaa")
    return crops.loc[ccaa, "grape"]


def get_crop_data(variety: str) -> dict:

    """
    Devuelve el perfil agronómico de una variedad concreta.
    """
    
    crop_df = pd.read_csv("data/grape_profiles.csv", index_col="grape_variety")

    matches = [v for v in crop_df.index if v.lower() == variety.strip().lower()]
    if not matches:
        raise ValueError(f"No existe la variedad '{variety}' en el dataset")

    row = crop_df.loc[matches[0]]
    return {
        "variety": matches[0],
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