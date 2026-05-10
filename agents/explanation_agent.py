from typing import List
from models.shared_state import SharedState, RiskLevel
from rag.graph.graph_retriever import get_graph_retriever, GraphContext
from rag.retriever import get_chroma_retriever
from smolagents import ChatMessage


class ExplanationAgent:

    def __init__(self, llm_client):
        self.llm = llm_client
        self.graph_retriever = get_graph_retriever()

        try:
            self.chroma_retriever = get_chroma_retriever()
        except Exception:
            self.chroma_retriever = None

    def run(self, state: SharedState) -> SharedState:
        scenarios = state.scenarios or []
        alerts = state.alerts or []

        graph_contexts = self._get_graph_contexts(alerts)

        explanation = {
            "summary": self._generate_summary(scenarios, alerts, graph_contexts, state.ccaa),
            "confidence": self._calculate_confidence(state),
            "risk_explanation": self._explain_risks(alerts, graph_contexts),
            "recommendation_reasoning": self._explain_recommendations(scenarios, graph_contexts),
            "alternatives": self._explain_alternatives(scenarios[1:] if len(scenarios) > 1 else []),
            "sms_text": self._generate_sms(scenarios, alerts, state.ccaa),
            "sources": self._collect_sources(graph_contexts),
        }

        state.explanation = explanation
        return state

    def _level_to_text(self, level):
        return level.value if isinstance(level, RiskLevel) else str(level)

    def _get_graph_contexts(self, alerts: List) -> dict[str, GraphContext]:
        contexts = {}
        for alert in alerts:
            if alert.risk_type not in contexts:
                ctx = self.graph_retriever.get_context_for_risk(alert.risk_type)
                if ctx:
                    contexts[alert.risk_type] = ctx
        return contexts

    def _generate_summary(self, scenarios, alerts, graph_contexts, ccaa):

        graph_info = "\n\n".join(
            ctx.to_prompt_context() for ctx in graph_contexts.values()
        )

        chroma_info = ""

        if self.chroma_retriever is not None and alerts:
            query = " ".join([a.risk_type for a in alerts[:2]])
            chroma_chunks = self.chroma_retriever.retrieve(query, top_k=2)
            chroma_info = self.chroma_retriever.format_context(chroma_chunks)

        recommended_actions = "N/A"
        if scenarios and scenarios[0].actions:
            recommended_actions = ", ".join(
                f"{a.type} ({a.intensity})"
                for a in scenarios[0].actions
            )

        risks_text = [
            f"{a.risk_type}: {self._level_to_text(a.level)}"
            for a in alerts
        ]

        prompt = f"""Eres un asesor vitícola experto. Genera un resumen de 2-3 frases para un viticultor en {ccaa}.

CONOCIMIENTO ESTRUCTURADO:
{graph_info if graph_info else "No hay riesgos relevantes en el grafo para este caso."}

DOCUMENTACIÓN TÉCNICA:
{chroma_info if chroma_info else "No hay documentación adicional disponible."}

SITUACIÓN ACTUAL:
- Región: {ccaa}
- Riesgos detectados: {risks_text if risks_text else "No hay riesgos destacados"}
- Escenario recomendado: {recommended_actions}

INSTRUCCIONES:
- No pidas más datos al usuario.
- Usa únicamente la información anterior.
- Sé directo, práctico y breve.
- Si no hay riesgos, indícalo claramente.
- Menciona la acción principal recomendada.
"""

        try:
            messages = [ChatMessage(role="user", content=prompt)]
            response = self.llm(messages)

            if hasattr(response, "content"):
                return response.content

            return str(response)

        except Exception:
            return f"En {ccaa}, se recomienda revisar las condiciones del cultivo."

    def _calculate_confidence(self, state):
        return {"score": 0.9, "label": "alta"}

    def _explain_risks(self, alerts, graph_contexts):

        result = []

        for alert in alerts[:3]:
            result.append({
                "type": alert.risk_type,
                "level": self._level_to_text(alert.level),
                "value": alert.value,
                "threshold": alert.threshold
            })

        return result

    def _explain_recommendations(self, scenarios, graph_contexts):
        return "Basado en el análisis de riesgos."

    def _generate_sms(self, scenarios, alerts, ccaa):
        if not alerts:
            return f"{ccaa}: sin alertas."

        return f"{ccaa}: {alerts[0].risk_type} {self._level_to_text(alerts[0].level)}"

    def _collect_sources(self, graph_contexts):
        sources = set()
        for c in graph_contexts.values():
            sources.update(c.sources)
        return list(sources)

    def _explain_alternatives(self, alternatives):
        return []