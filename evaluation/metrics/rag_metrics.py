"""
rag_metrics.py
--------------
Evalúa el sistema RAG híbrido del ExplanationAgent.

Mide tres cosas:
  1. Cobertura del grafo: para cada tipo de riesgo del sistema,
     ¿existe un nodo en el grafo con causas, efectos y mitigaciones?
  2. Tasa de recuperación del GraphRetriever: porcentaje de llamadas
     a get_context_for_risk() que devuelven un GraphContext no nulo.
  3. Riqueza del contexto: cuántas causas, efectos y acciones
     tiene cada nodo del grafo.

Uso:
    python evaluation/metrics/rag_metrics.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rag.graph.graph_retriever import get_graph_retriever
from rag.graph.schema import RISK_TO_NODE_MAPPING


def evaluate_graph_coverage() -> dict:
    """
    Para cada tipo de riesgo del sistema, comprueba si el grafo
    tiene información suficiente.

    Umbral mínimo:
      - Al menos 1 causa
      - Al menos 1 efecto
      - Al menos 1 acción de mitigación
    """
    retriever = get_graph_retriever()
    resultados = {}

    print("\n" + "="*60)
    print("COBERTURA DEL GRAFO DE CONOCIMIENTO")
    print("="*60)
    print(f"{'Riesgo':<25} {'Nodo':<20} {'Causas':>7} {'Efectos':>8} {'Mitig.':>7} {'OK':>4}")
    print("-"*60)

    total_ok = 0

    for risk_key, node_id in RISK_TO_NODE_MAPPING.items():
        context = retriever.get_context_for_risk(risk_key)

        if context is None:
            resultados[risk_key] = {
                "node_id":    node_id,
                "found":      False,
                "n_causes":   0,
                "n_effects":  0,
                "n_mitig":    0,
                "coverage_ok": False,
            }
            print(f"{risk_key:<25} {'— NO ENCONTRADO':<20} {'':>7} {'':>8} {'':>7} {'✗':>4}")
            continue

        n_causes  = len(context.causes)
        n_effects = len(context.effects)
        n_mitig   = len(context.mitigations)
        ok = n_causes >= 1 and n_effects >= 1 and n_mitig >= 1

        if ok:
            total_ok += 1

        resultados[risk_key] = {
            "node_id":     node_id,
            "found":       True,
            "label":       context.risk_label,
            "n_causes":    n_causes,
            "n_effects":   n_effects,
            "n_mitig":     n_mitig,
            "coverage_ok": ok,
            "sources":     len(context.sources),
        }

        status = "✓" if ok else "✗"
        print(f"{risk_key:<25} {node_id:<20} {n_causes:>7} {n_effects:>8} "
              f"{n_mitig:>7} {status:>4}")

    total    = len(RISK_TO_NODE_MAPPING)
    cobertura = total_ok / total if total > 0 else 0

    print("-"*60)
    print(f"Cobertura total: {total_ok}/{total} ({cobertura:.0%})")
    print("="*60)

    return {
        "por_riesgo":    resultados,
        "total_riesgos": total,
        "riesgos_ok":    total_ok,
        "cobertura_pct": round(cobertura * 100, 1),
    }


def evaluate_retrieval_rate() -> dict:
    """
    Llama a get_context_for_risk() para cada riesgo del sistema
    y mide la tasa de recuperación (cuántas devuelven contexto no nulo).
    """
    retriever = get_graph_retriever()
    encontrados = 0
    total = len(RISK_TO_NODE_MAPPING)

    for risk_key in RISK_TO_NODE_MAPPING:
        ctx = retriever.get_context_for_risk(risk_key)
        if ctx is not None:
            encontrados += 1

    tasa = encontrados / total if total > 0 else 0

    print(f"\nTasa de recuperación GraphRetriever: "
          f"{encontrados}/{total} ({tasa:.0%})")

    return {
        "encontrados": encontrados,
        "total":       total,
        "tasa_pct":    round(tasa * 100, 1),
    }


def evaluate_chroma_coverage() -> dict:
    """
    Verifica que ChromaDB está operativo y tiene documentos ingestados.
    """
    try:
        from rag.retriever import get_chroma_retriever
        retriever = get_chroma_retriever()
        n_docs = retriever.count

        print(f"\nChromaDB: {n_docs} fragmentos ingestados")

        # Test de recuperación con una consulta de prueba
        chunks = retriever.retrieve("riesgo mildiu humedad", top_k=3)
        print(f"Test de consulta: {len(chunks)} chunks recuperados")

        return {
            "n_documentos": n_docs,
            "test_chunks":  len(chunks),
            "operativo":    n_docs > 0,
        }
    except Exception as e:
        print(f"\nChromaDB no disponible: {e}")
        return {"operativo": False, "error": str(e)}


if __name__ == "__main__":
    graph_result = evaluate_graph_coverage()
    retrieval    = evaluate_retrieval_rate()
    chroma       = evaluate_chroma_coverage()

    print("\n" + "="*60)
    print("RESUMEN RAG")
    print("="*60)
    print(f"Cobertura del grafo:        {graph_result['cobertura_pct']}%")
    print(f"Tasa recuperación grafo:    {retrieval['tasa_pct']}%")
    print(f"ChromaDB operativo:         {'Sí' if chroma.get('operativo') else 'No'}")
    if chroma.get("operativo"):
        print(f"Documentos en ChromaDB:     {chroma['n_documentos']}")
    print("="*60)