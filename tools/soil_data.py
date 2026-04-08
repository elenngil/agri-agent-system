import pandas as pd
from tools.aemet_stations import get_stations
from tools.aemet_stations import station_to_ccaa

data = {
    "ccaa": ["Andalucía", "Aragón", "Asturias", "Baleares", "Canarias", "Cantabria", "Castilla-La Mancha", "Castilla y León", "Cataluña", "Comunidad Valenciana", "Extremadura", "Galicia", "La Rioja", "Madrid", "Murcia", "Navarra", "País Vasco"],
    "soil_type": ["Calcáreo", "Pizarra", "Arenoso", "Calizo", "Volcánico", "Arenoso", "Arcilloso", "Arcilloso", "Pizarra", "Calcáreo", "Arcilloso", "Granítico", "Calcáreo", "Granítico", "Arcilloso", "Aluvial", "Calcáreo"]
}

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

    data = get_stations()

    soils = {
    "ccaa": ["Andalucía", "Aragón", "Asturias", "Baleares", "Canarias", "Cantabria", "Castilla-La Mancha", "Castilla y León", "Cataluña", "Comunidad Valenciana", "Extremadura", "Galicia", "La Rioja", "Madrid", "Murcia", "Navarra", "País Vasco"],
    "soil_type": ["Calcáreo", "Pizarra", "Arenoso", "Calizo", "Volcánico", "Arenoso", "Arcilloso", "Arcilloso", "Pizarra", "Calcáreo", "Arcilloso", "Granítico", "Calcáreo", "Granítico", "Arcilloso", "Aluvial", "Calcáreo"]
    }

    mult = {"Arenoso": 1.3, "Arcilloso": 0.7, "Calcáreo": 1.0, "Pizarra": 1.1, "Volcánico": 1.0, "Granítico": 1.1, "Aluvial": 0.9, 'Calizo': 1.0}

    ccaa = station_to_ccaa(station)
    soil_type = soils["soil_type"][soils["ccaa"].index(ccaa)]

    return mult[soil_type]

#print(get_soil_multiplier("B013X"))



        

