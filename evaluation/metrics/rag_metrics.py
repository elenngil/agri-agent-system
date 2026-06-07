import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rag.graph.graph_retriever import get_graph_retriever
from rag.graph.schema import RISK_TO_NODE_MAPPING


def evaluate_graph_coverage() -> dict:
    retriever = get_graph_retriever()
    resultados = {}

    print("\n" + "="*60)
    print("COBERTURA DEL GRAFO DE CONOCIMIENTO")
    print("="*60)
    print(f"{'Riesgo':<25} {'Nodo':<20} {'Causas':>7} "
          f"{'Efectos':>8} {'Mitig.':>7} {'OK':>4}")
    print("-"*60)

    total_ok = 0

    for risk_key, node_id in RISK_TO_NODE_MAPPING.items():
        context = retriever.get_context_for_risk(risk_key)

        if context is None:
            resultados[risk_key] = {
                "node_id": node_id, "found": False,
                "n_causes": 0, "n_effects": 0,
                "n_mitig": 0, "coverage_ok": False,
            }
            print(f"{risk_key:<25} {'— NO ENCONTRADO':<20} {'':>7} "
                  f"{'':>8} {'':>7} {'x':>4}")
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

        status = "ok" if ok else "x"
        print(f"{risk_key:<25} {node_id:<20} {n_causes:>7} "
              f"{n_effects:>8} {n_mitig:>7} {status:>4}")

    total     = len(RISK_TO_NODE_MAPPING)
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
    retriever   = get_graph_retriever()
    encontrados = 0
    total       = len(RISK_TO_NODE_MAPPING)

    for risk_key in RISK_TO_NODE_MAPPING:
        ctx = retriever.get_context_for_risk(risk_key)
        if ctx is not None:
            encontrados += 1

    tasa = encontrados / total if total > 0 else 0

    print(f"\nTasa de recuperacion GraphRetriever: "
          f"{encontrados}/{total} ({tasa:.0%})")

    return {
        "encontrados": encontrados,
        "total":       total,
        "tasa_pct":    round(tasa * 100, 1),
    }


if __name__ == "__main__":
    graph_result = evaluate_graph_coverage()
    retrieval    = evaluate_retrieval_rate()

    print("\n" + "="*60)
    print("RESUMEN RAG")
    print("="*60)
    print(f"Cobertura del grafo:     {graph_result['cobertura_pct']}%")
    print(f"Tasa recuperacion grafo: {retrieval['tasa_pct']}%")
    print("="*60)