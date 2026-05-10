from enum import Enum
from dataclasses import dataclass
from typing import Optional


class NodeType(Enum):
    VARIABLE_CLIMATICA = "variable_climatica"
    RIESGO = "riesgo"
    ENFERMEDAD = "enfermedad"
    COMPONENTE_VID = "componente_vid"
    FASE_FENOLOGICA = "fase_fenologica"
    ACCION = "accion"
    UMBRAL = "umbral"


class RelationType(Enum):
    CAUSA = "causa"
    PROVOCA = "provoca"
    FAVORECE = "favorece"
    INHIBE = "inhibe"

    DAÑA = "daña"
    REDUCE = "reduce"
    AUMENTA = "aumenta"

    VULNERABLE_EN = "vulnerable_en"

    MITIGA = "mitiga"
    PREVIENE = "previene"
    REQUIERE = "requiere"

    INDICA = "indica"
    SE_DETECTA_POR = "se_detecta_por"


# ✅ CLAVE (esto es lo importante)
CAUSE_RELATIONS = {
    RelationType.CAUSA.value,
    RelationType.PROVOCA.value,
    RelationType.FAVORECE.value,
}

EFFECT_RELATIONS = {
    RelationType.DAÑA.value,
    RelationType.REDUCE.value,
    RelationType.AUMENTA.value,
}

MITIGATION_RELATIONS = {
    RelationType.MITIGA.value,
    RelationType.PREVIENE.value,
    RelationType.INHIBE.value,
}


RISK_TO_NODE_MAPPING = {
    "frost_risk": "helada",
    "mildiu_risk": "mildiu",
    "heat_stress": "estres_termico",
    "future_water_stress": "estres_hidrico",
    "strong_wind_risk": "riesgo_viento",
}