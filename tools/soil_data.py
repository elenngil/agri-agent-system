import pandas as pd
from tools.aemet_stations import get_stations
from tools.aemet_stations import station_to_ccaa

'''
Se podrá utilizar el irrigation_multiplier para ajustar la cantidad de agua necesaria según el tipo de suelo.
Para saber que tipo de suelo es, se podría usar la ubicación del usuario que pondrá con el indicador de la estación (comunidad autónoma) para determinar el tipo de suelo predominante en esa región.
'''


def get_soil_multiplier(station: str) -> float:
    """
    Get an irrigation multiplier based on the predominant soil type in the region
    of the given weather station.

    Args:
        station: Weather station ID.

    Returns:
        Irrigation multiplier associated with the soil type of the station region.
    """

    mult = {"arenoso": 1.3, "arcilloso": 0.7, "pizarra": 1.1, "volcanico": 1.0, "granitico": 1.1, "aluvial": 0.9, 'calizo': 1.0}

    ccaa = station_to_ccaa(station)
    grape = pd.read_csv("data/ccaa_grape.csv", index_col="ccaa")["grape"].to_dict()[ccaa]
    soil_type = pd.read_csv("data/grape_profiles.csv", index_col="grape_variety")["soil"].to_dict()[grape]
    #soil_type = pd.read_csv("data/.csv")
    #soil_type = soils["soil_type"][soils["ccaa"].index(ccaa)]

    return mult[soil_type]

#print(get_soil_multiplier("B013X"))




        

