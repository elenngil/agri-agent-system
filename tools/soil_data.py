import pandas as pd
from tools.aemet_stations import station_to_ccaa


MULTIPLIERS = {
    "arenoso":   1.3,
    "franco":    1.0,
    "arcilloso": 0.7,
    "pizarra":   1.1,
    "volcanico": 1.0,
    "granitico": 1.1,
    "aluvial":   0.9,
    "calizo":    1.0,
}

def get_soil_from_ccaa(station: str) -> str:

    ccaa      = station_to_ccaa(station)
    grape_df  = pd.read_csv("data/ccaa_grape.csv",     index_col="ccaa")
    soil_df   = pd.read_csv("data/grape_profiles.csv", index_col="grape_variety")
    grape     = grape_df.loc[ccaa, "grape"]
    soil      = soil_df.loc[grape, "soil"]
    return soil.strip().lower()


def get_soil_multiplier(soil_type: str) -> float:

    return MULTIPLIERS.get(soil_type.strip().lower(), 1.0)