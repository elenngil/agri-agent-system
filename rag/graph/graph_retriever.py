import json
import networkx as nx
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from .schema import (
    RelationType,
    RISK_TO_NODE_MAPPING,
    CAUSE_RELATIONS,
    EFFECT_RELATIONS,
    MITIGATION_RELATIONS,
)


@dataclass
class GraphContext:
    risk_id: str
    risk_label: str
    risk_description: str
    
    causes: List[dict]
    effects: List[dict]
    vulnerable_phases: List[dict]
    mitigations: List[dict]
    sources: List[str]
    
    def to_prompt_context(self) -> str:
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
        node_id = RISK_TO_NODE_MAPPING.get(risk_key)
        if not node_id or node_id not in self.graph:
            return None
        
        node_data = self.graph.nodes[node_id]
        sources = []
        
        if node_data.get("source"):
            sources.append(node_data["source"])
        
        causes = []
        for predecessor in self.graph.predecessors(node_id):
            edge = self.graph.edges[predecessor, node_id]
            pred_data = self.graph.nodes[predecessor]
            
            if edge["type"] in CAUSE_RELATIONS:
                causes.append({
                    "id": predecessor,
                    "label": pred_data.get("label", predecessor),
                    "relation": edge["type"],
                    "weight": edge.get("weight", 1.0),
                    "condition": edge.get("condition")
                })
                if edge.get("source_ref"):
                    sources.append(edge["source_ref"])
        
        effects = []
        for successor in self.graph.successors(node_id):
            edge = self.graph.edges[node_id, successor]
            succ_data = self.graph.nodes[successor]
            
            if edge["type"] in EFFECT_RELATIONS:
                effects.append({
                    "id": successor,
                    "label": succ_data.get("label", successor),
                    "relation": edge["type"],
                    "weight": edge.get("weight", 1.0),
                    "condition": edge.get("condition")
                })
                if edge.get("source_ref"):
                    sources.append(edge["source_ref"])
        
        vulnerable_phases = []
        for successor in self.graph.successors(node_id):
            edge = self.graph.edges[node_id, successor]
            succ_data = self.graph.nodes[successor]
            
            if edge["type"] == RelationType.VULNERABLE_EN.value:
                vulnerable_phases.append({
                    "id": successor,
                    "label": succ_data.get("label", successor),
                    "condition": edge.get("condition")
                })
                if edge.get("source_ref"):
                    sources.append(edge["source_ref"])
        
        mitigations = []
        for predecessor in self.graph.predecessors(node_id):
            edge = self.graph.edges[predecessor, node_id]
            pred_data = self.graph.nodes[predecessor]
            
            if edge["type"] in MITIGATION_RELATIONS:
                mitigations.append({
                    "id": predecessor,
                    "label": pred_data.get("label", predecessor),
                    "relation": edge["type"],
                    "weight": edge.get("weight", 1.0),
                    "condition": edge.get("condition")
                })
                if edge.get("source_ref"):
                    sources.append(edge["source_ref"])
        
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
        context = self.get_context_for_risk(risk_key)
        if not context:
            return []
        return context.mitigations
    
    def get_related_risks(self, risk_key: str) -> List[str]:
        node_id = RISK_TO_NODE_MAPPING.get(risk_key)
        if not node_id:
            return []
        
        related = set()
        
        for predecessor in self.graph.predecessors(node_id):
            for other in self.graph.successors(predecessor):
                other_data = self.graph.nodes.get(other, {})
                if other_data.get("type") == "riesgo" and other != node_id:
                    related.add(other)
        
        return list(related)
    
    def explain_causal_chain(self, risk_key: str) -> str:
        context = self.get_context_for_risk(risk_key)
        if not context:
            return f"No se encontró información para el riesgo: {risk_key}"
        
        return context.to_prompt_context()


_retriever_instance: Optional[GraphRetriever] = None

def get_graph_retriever() -> GraphRetriever:
    """Obtiene instancia singleton del retriever."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = GraphRetriever()
    return _retriever_instance
