"""
Esquema del grafo de conocimiento agrícola.
Define los tipos de nodos y relaciones válidos.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class NodeType(Enum):
    """Tipos de nodos en el grafo de conocimiento."""
    
    # Variables ambientales medibles
    VARIABLE_CLIMATICA = "variable_climatica"
    
    # Riesgos que el sistema puede detectar
    RIESGO = "riesgo"
    
    # Enfermedades o plagas
    ENFERMEDAD = "enfermedad"
    
    # Partes o estados de la vid
    COMPONENTE_VID = "componente_vid"
    
    # Fases del ciclo de la vid
    FASE_FENOLOGICA = "fase_fenologica"
    
    # Acciones que puede tomar el agricultor
    ACCION = "accion"
    
    # Umbrales numéricos
    UMBRAL = "umbral"


class RelationType(Enum):
    """Tipos de relaciones entre nodos."""
    
    # Causalidad
    CAUSA = "causa"                    # A causa B
    PROVOCA = "provoca"                # A provoca B (similar pero más directo)
    
    # Favorabilidad
    FAVORECE = "favorece"              # A favorece B (condición propicia)
    INHIBE = "inhibe"                  # A inhibe B
    
    # Efectos
    DAÑA = "daña"                      # A daña B
    REDUCE = "reduce"                  # A reduce B
    AUMENTA = "aumenta"                # A aumenta B
    
    # Vulnerabilidad temporal
    VULNERABLE_EN = "vulnerable_en"    # A es vulnerable en fase B
    
    # Recomendaciones
    MITIGA = "mitiga"                  # Acción A mitiga riesgo B
    PREVIENE = "previene"              # Acción A previene B
    REQUIERE = "requiere"              # A requiere acción B
    
    # Detección
    INDICA = "indica"                  # Variable A indica riesgo B
    SE_DETECTA_POR = "se_detecta_por"  # A se detecta por variable B


@dataclass
class Node:
    """Representa un nodo en el grafo."""
    id: str                            # Identificador único (ej: "mildiu")
    type: NodeType                     # Tipo de nodo
    label: str                         # Nombre legible (ej: "Mildiu")
    description: Optional[str] = None  # Descripción opcional
    source: Optional[str] = None       # Fuente bibliográfica
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "label": self.label,
            "description": self.description,
            "source": self.source
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Node":
        return cls(
            id=data["id"],
            type=NodeType(data["type"]),
            label=data["label"],
            description=data.get("description"),
            source=data.get("source")
        )


@dataclass
class Relation:
    """Representa una relación dirigida entre dos nodos."""
    source_id: str                     # Nodo origen
    target_id: str                     # Nodo destino
    type: RelationType                 # Tipo de relación
    weight: float = 1.0                # Peso/fuerza de la relación (0-1)
    condition: Optional[str] = None    # Condición para que aplique
    source: Optional[str] = None       # Fuente bibliográfica
    
    def to_dict(self) -> dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.type.value,
            "weight": self.weight,
            "condition": self.condition,
            "source_ref": self.source
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Relation":
        return cls(
            source_id=data["source"],
            target_id=data["target"],
            type=RelationType(data["type"]),
            weight=data.get("weight", 1.0),
            condition=data.get("condition"),
            source=data.get("source_ref")
        )


# Mapeo de riesgos del sistema a nodos del grafo
RISK_TO_NODE_MAPPING = {
    "frost_risk": "helada",
    "mildiu_risk": "mildiu", 
    "heat_stress": "estres_termico",
    "future_water_stress": "estres_hidrico",
    "strong_wind_risk": "viento_fuerte"
}
