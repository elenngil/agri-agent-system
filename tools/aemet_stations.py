from tools.aemet_api import aemet_get
import pandas as pd
from functools import lru_cache

@lru_cache(maxsize=1)
def get_stations():
    data = aemet_get("valores/climatologicos/inventarioestaciones/todasestaciones")
    df = pd.DataFrame(data)[["indicativo", "nombre", "provincia"]]
    df = df.rename(columns={"indicativo": "id"})
    return df


def station_to_ccaa(station: str):

    data = get_stations()
    row = data[data["id"] == station]

    if row.empty:
        raise ValueError(f"No encuentro la estación {station} en el inventario de AEMET")

    provincia = row["provincia"].values[0].strip().upper()
    ccaa = " "

    match provincia:
        case "ILLES BALEARS" | "BALEARES":
            ccaa = "Baleares"
        case "LAS PALMAS" | "SANTA CRUZ DE TENERIFE" | "STA. CRUZ DE TENERIFE":
            ccaa = "Canarias"
        case "TARRAGONA" | "LLEIDA" | "BARCELONA"| "GIRONA":
            ccaa = "Cataluña"
        case "NAVARRA":
            ccaa = "Navarra"
        case "GIPUZKOA" | "ARABA/ALAVA" | "BIZKAIA":
            ccaa = "País Vasco"
        case "CANTABRIA":
            ccaa = "Cantabria"
        case "ASTURIAS":
            ccaa = "Asturias"
        case "LEON" | "ZAMORA" | "SALAMANCA" | "BURGOS" | "PALENCIA" | "SORIA" | "SEGOVIA" | "AVILA" | "VALLADOLID":
            ccaa = "Castilla y León"
        case "LUGO" | "A CORUÑA" | "PONTEVEDRA" | "OURENSE":
            ccaa = "Galicia"
        case "MADRID":
            ccaa = "Madrid"
        case "GUADALAJARA" | "TOLEDO" | "CIUDAD REAL" | "CUENCA" | "ALBACETE":
            ccaa = "Castilla-La Mancha"
        case "CACERES" | "BADAJOZ":
            ccaa = "Extremadura"
        case  "CORDOBA" | "SEVILLA" | "JAEN" | "HUELVA" | "ALMERIA" | "GRANADA" | "MALAGA" | "CADIZ":
            ccaa = "Andalucía"
        case "MURCIA":
            ccaa = "Murcia"
        case "ALICANTE" | "CASTELLON" | "VALENCIA":
            ccaa = "Comunidad Valenciana"
        case "TERUEL" | "HUESCA" | "ZARAGOZA":
            ccaa = "Aragón"
        case "LA RIOJA":
            ccaa = "La Rioja"

    return ccaa


    