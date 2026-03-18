from smolagents import tool
from tools.aemet_stations import station_to_ccaa
import pandas as pd

@tool
def get_crop_data(station: str) -> dict:
    '''
    Obtiene información sobre un tipo de cultivo específico.
    Args:
        station (str): La estación para la cual se desea obtener información.
    Returns:
        dict: Un diccionario que contiene información relevante sobre el cultivo, como sus necesidades de agua, temperatura óptima, etc.
    '''
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
        "País Vasco": "Tempranillo"
    }
    
    ccaa = station_to_ccaa(station)
    crop_type = crops[ccaa]

    crop_df = pd.read_csv("data/grape_profiles.csv", index_col="grape_variety")
    
    if crop_type not in crop_df.index:
        raise ValueError(f"No encuentro información sobre el cultivo asociado a la estación {station} (CCAA: {ccaa})")
    else:
        crop_info = crop_df.loc[crop_type].to_dict()
        return crop_info




