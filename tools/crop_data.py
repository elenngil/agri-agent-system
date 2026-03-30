import pandas as pd
from smolagents import tool
from tools.aemet_stations import station_to_ccaa


@tool
def get_crop_data(station: str) -> dict:
    """
    Obtiene información del cultivo asociado a una estación meteorológica.

    Args:
        station: ID de la estación meteorológica.

    Returns:
        Un diccionario con la variedad de cultivo y sus características agronómicas.
    """
    crops = {
        "Andalucía": "Pedro Ximenez",
        "Aragón": "Garnacha",
        "Asturias": "Albariño",
        "Baleares": "Mencia",
        "Canarias": "Palomino",
        "Cantabria": "Albariño",
        "Castilla-La Mancha": "Airen",
        "Castilla y León": "Tempranillo",
        "Cataluña": "Macabeo",
        "Comunidad Valenciana": "Bobal",
        "Extremadura": "Pardina",
        "Galicia": "Albariño",
        "La Rioja": "Tempranillo",
        "Madrid": "Garnacha",
        "Murcia": "Monastrell",
        "Navarra": "Tempranillo",
        "País Vasco": "Tempranillo",
    }

    ccaa = station_to_ccaa(station)
    crop_type = crops.get(ccaa)

    if crop_type is None:
        raise ValueError(f"No hay cultivo asociado a la CCAA de la estación {station}")

    crop_df = pd.read_csv("data/grape_profiles.csv", index_col="grape_variety")

    if crop_type not in crop_df.index:
        raise ValueError(
            f"No encuentro información sobre el cultivo asociado a la estación {station} "
            f"(CCAA: {ccaa}, cultivo: {crop_type})"
        )

    row = crop_df.loc[crop_type]

    crop_info = {
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

    return crop_info