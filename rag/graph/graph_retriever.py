"""
Módulo de consultas al grafo de conocimiento.

Proporciona funciones para extraer información estructurada
dado un riesgo, variable climática o consulta general.
"""

import json
import networkx as nx
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from .schema import NodeType, RelationType, RISK_TO_NODE_MAPPING


@dataclass
class GraphContext:
    """Contexto estructurado extraído del grafo."""
    risk_id: str
    risk_label: str
    risk_description: str
    
    # Qué lo causa
    causes: List[dict]
    
    # Qué efectos tiene
    effects: List[dict]
    
    # En qué fases es más peligroso
    vulnerable_phases: List[dict]
    
    # Qué acciones lo mitigan
    mitigations: List[dict]
    
    # Fuentes bibliográficas
    sources: List[str]
    
    def to_prompt_context(self) -> str:
        """Convierte el contexto a texto para usar en prompts de LLM."""
        lines = [f"## Información sobre: {self.risk_label}\n"]
        
        if self.risk_description:
            lines.append(f"{self.risk_description}\n")
        
        if self.causes:
            lines.append("### Causas:")
            for c in self.causes:
                cond = f" ({c['condition']})" if c.get('condition') else ""
                lines.append(f"- {c['label']}{cond}")
        
        if self.effects:
            lines.append("\n### Efectos en la vid:")
            for e in self.effects:
                rel = e.get('relation', 'afecta')
                cond = f" — {e['condition']}" if e.get('condition') else ""
                lines.append(f"- {rel.capitalize()} {e['label']}{cond}")
        
        if self.vulnerable_phases:
            lines.append("\n### Fases de mayor vulnerabilidad:")
            for p in self.vulnerable_phases:
                cond = f": {p['condition']}" if p.get('condition') else ""
                lines.append(f"- {p['label']}{cond}")
        
        if self.mitigations:
            lines.append("\n### Acciones recomendadas:")
            for m in self.mitigations:
                cond = f" ({m['condition']})" if m.get('condition') else ""
                lines.append(f"- {m['label']}{cond}")
        
        if self.sources:
            lines.append("\n### Fuentes:")
            for s in sorted(set(self.sources)):
                lines.append(f"- {s}")
        
        return "\n".join(lines)


class GraphRetriever:
    """Recupera información del grafo de conocimiento."""
    
    def __init__(self, graph_path: Optional[str | Path] = None):
        if graph_path is None:
            graph_path = Path(__file__).parent / "knowledge_graph.json"
        
        self.graph = nx.DiGraph()
        self._load_graph(graph_path)
    
    def _load_graph(self, filepath: str | Path) -> None:
        """Carga el grafo desde JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for node in data["nodes"]:
            self.graph.add_node(node["id"], **node)
        
        for rel in data["relations"]:
            self.graph.add_edge(
                rel["source"], 
                rel["target"],
                type=rel["type"],
                weight=rel.get("weight", 1.0),
                condition=rel.get("condition"),
                source_ref=rel.get("source_ref")
            )
    
    def get_context_for_risk(self, risk_key: str) -> Optional[GraphContext]:
        """
        Obtiene contexto completo para un riesgo del sistema.
        
        Args:
            risk_key: Clave del riesgo como viene del RiskAgent
                     (ej: "frost_risk", "mildiu_risk")
        
        Returns:
            GraphContext con toda la información relacionada
        """
        # Mapear clave del sistema a nodo del grafo
        node_id = RISK_TO_NODE_MAPPING.get(risk_key)
        if not node_id or node_id not in self.graph:
            return None
        
        node_data = self.graph.nodes[node_id]
        sources = []
        
        if node_data.get("source"):
            sources.append(node_data["source"])
        
        # Obtener causas (qué apunta hacia este riesgo)
        causes = []
        for predecessor in self.graph.predecessors(node_id):
            edge = self.graph.edges[predecessor, node_id]
            pred_data = self.graph.nodes[predecessor]
            
            if edge["type"] in ("causa", "provoca", "favorece"):
                causes.append({
                    "id": predecessor,
                    "label": pred_data.get("label", predecessor),
                    "relation": edge["type"],
                    "weight": edge.get("weight", 1.0),
                    "condition": edge.get("condition")
                })
                if edge.get("source_ref"):
                    sources.append(edge["source_ref"])
        
        # Obtener efectos (hacia dónde apunta este riesgo)
        effects = []
        for successor in self.graph.successors(node_id):
            edge = self.graph.edges[node_id, successor]
            succ_data = self.graph.nodes[successor]
            
            if edge["type"] in ("daña", "reduce", "aumenta"):
                effects.append({
                    "id": successor,
                    "label": succ_data.get("label", successor),
                    "relation": edge["type"],
                    "weight": edge.get("weight", 1.0),
                    "condition": edge.get("condition")
                })
                if edge.get("source_ref"):
                    sources.append(edge["source_ref"])
        
        # Obtener fases vulnerables
        vulnerable_phases = []
        for successor in self.graph.successors(node_id):
            edge = self.graph.edges[node_id, successor]
            succ_data = self.graph.nodes[successor]
            
            if edge["type"] == "vulnerable_en":
                vulnerable_phases.append({
                    "id": successor,
                    "label": succ_data.get("label", successor),
                    "condition": edge.get("condition")
                })
                if edge.get("source_ref"):
                    sources.append(edge["source_ref"])
        
        # Obtener acciones que mitigan
        mitigations = []
        for predecessor in self.graph.predecessors(node_id):
            edge = self.graph.edges[predecessor, node_id]
            pred_data = self.graph.nodes[predecessor]
            
            if edge["type"] in ("mitiga", "previene", "inhibe"):
                mitigations.append({
                    "id": predecessor,
                    "label": pred_data.get("label", predecessor),
                    "relation": edge["type"],
                    "weight": edge.get("weight", 1.0),
                    "condition": edge.get("condition")
                })
                if edge.get("source_ref"):
                    sources.append(edge["source_ref"])
        
        # Ordenar por peso (relevancia)
        causes.sort(key=lambda x: x["weight"], reverse=True)
        effects.sort(key=lambda x: x["weight"], reverse=True)
        mitigations.sort(key=lambda x: x["weight"], reverse=True)
        
        return GraphContext(
            risk_id=node_id,
            risk_label=node_data.get("label", node_id),
            risk_description=node_data.get("description", ""),
            causes=causes,
            effects=effects,
            vulnerable_phases=vulnerable_phases,
            mitigations=mitigations,
            sources=sources
        )
    
    def get_actions_for_risk(self, risk_key: str) -> List[dict]:
        """
        Obtiene solo las acciones recomendadas para un riesgo.
        Útil para el DeliberativeAgent.
        """
        context = self.get_context_for_risk(risk_key)
        if not context:
            return []
        return context.mitigations
    
    def get_related_risks(self, risk_key: str) -> List[str]:
        """
        Obtiene riesgos relacionados (comparten causas o efectos).
        """
        node_id = RISK_TO_NODE_MAPPING.get(risk_key)
        if not node_id:
            return []
        
        related = set()
        
        # Riesgos que comparten causas
        for predecessor in self.graph.predecessors(node_id):
            for other in self.graph.successors(predecessor):
                other_data = self.graph.nodes.get(other, {})
                if other_data.get("type") == "riesgo" and other != node_id:
                    related.add(other)
        
        return list(related)
    
    def explain_causal_chain(self, risk_key: str) -> str:
        """
        Genera una explicación de la cadena causal para un riesgo.
        Útil para el ExplanationAgent.
        """
        context = self.get_context_for_risk(risk_key)
        if not context:
            return f"No se encontró información para el riesgo: {risk_key}"
        
        return context.to_prompt_context()


# Singleton para reutilizar
_retriever_instance: Optional[GraphRetriever] = None

def get_retriever() -> GraphRetriever:
    """Obtiene instancia singleton del retriever."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = GraphRetriever()
    return _retriever_instance
