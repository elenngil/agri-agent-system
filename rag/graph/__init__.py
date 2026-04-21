"""
Graph RAG - Grafo de conocimiento vitícola.

Uso básico:
    from rag.graph import get_retriever
    
    retriever = get_retriever()
    context = retriever.get_context_for_risk("frost_risk")
    print(context.to_prompt_context())
"""

from .schema import NodeType, RelationType, Node, Relation, RISK_TO_NODE_MAPPING
from .graph_retriever import GraphRetriever, GraphContext, get_retriever
from .graph_builder import KnowledgeGraphBuilder, build_viticulture_graph

__all__ = [
    "NodeType",
    "RelationType", 
    "Node",
    "Relation",
    "RISK_TO_NODE_MAPPING",
    "GraphRetriever",
    "GraphContext",
    "get_retriever",
    "KnowledgeGraphBuilder",
    "build_viticulture_graph",
]
