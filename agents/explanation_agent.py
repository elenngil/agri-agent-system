# agents/explanation_agent.py

from typing import List, Optional
from models.shared_state import SharedState
from rag.graph import get_retriever, GraphContext


class ExplanationAgent:
    """
    Genera explicaciones en lenguaje natural para las recomendaciones.
    
    Usa el Graph RAG para obtener contexto estructurado sobre los riesgos
    y generar explicaciones más precisas y fundamentadas.
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.graph_retriever = get_retriever()
    
    def run(self, state: SharedState) -> SharedState:
        scenarios = state.scenarios or []
        alerts = state.alerts or []

        graph_contexts = self._get_graph_contexts(alerts)
        
        explanation = {
            "summary": self._generate_summary(scenarios, alerts, graph_contexts, state.ccaa),
            "risk_explanation": self._explain_risks(alerts, graph_contexts),
            "recommendation_reasoning": self._explain_recommendations(scenarios, graph_contexts),
            "alternatives": self._explain_alternatives(scenarios[1:] if len(scenarios) > 1 else []),
            "sms_text": self._generate_sms(scenarios, alerts, state.ccaa),
            "sources": self._collect_sources(graph_contexts),
        }
        
        state.explanation = explanation
        return state
    
    def _get_graph_contexts(self, alerts: List) -> dict[str, GraphContext]:
        """Obtiene contexto del grafo para cada tipo de riesgo en las alertas."""
        contexts = {}
        for alert in alerts:
            risk_type = alert.risk_type
            if risk_type not in contexts:
                context = self.graph_retriever.get_context_for_risk(risk_type)
                if context:
                    contexts[risk_type] = context
        return contexts
    
    def _generate_summary(self, scenarios, alerts, graph_contexts, ccaa) -> str:
        """Genera resumen usando el LLM con contexto del grafo."""
        
        graph_info = "\n\n".join([
            ctx.to_prompt_context()
            for ctx in graph_contexts.values()
        ])

        recommended_actions = "N/A"
        if scenarios and scenarios[0].actions:
            recommended_actions = ", ".join(
                f"{a.type} ({a.intensity})" for a in scenarios[0].actions
            )

        prompt = f"""Eres un asesor vitícola experto. Genera un resumen de 2-3 frases 
para un viticultor en {ccaa}.

CONTEXTO DEL CONOCIMIENTO VITÍCOLA:
{graph_info}

SITUACIÓN ACTUAL:
- Riesgos detectados: {[f"{a.risk_type}: {a.level}" for a in alerts]}
- Escenario recomendado: {recommended_actions}

INSTRUCCIONES:
- Sé directo y práctico
- Menciona el riesgo principal y la acción más importante
- No uses tecnicismos innecesarios
- Basa tu respuesta en el conocimiento proporcionado
"""

        messages = [{"role": "user", "content": prompt}]
        response = self.llm.generate(messages)

        if isinstance(response, str):
            return response

        if hasattr(response, "content"):
            return response.content

        return str(response)
    
    def _explain_risks(self, alerts, graph_contexts) -> List[dict]:
        """Explicación detallada de cada riesgo usando el grafo."""
        explanations = []
        
        for alert in alerts[:3]:  # Top 3 riesgos
            context = graph_contexts.get(alert.risk_type)
            
            explanation = {
                "type": alert.risk_type,
                "level": alert.level,
                "value": alert.value,
                "threshold": alert.threshold,
            }
            
            if context:
                # Añadir información del grafo
                explanation["description"] = context.risk_description
                explanation["causes"] = [
                    {"label": c["label"], "condition": c.get("condition")}
                    for c in context.causes[:2]
                ]
                explanation["effects"] = [
                    {"label": e["label"], "relation": e["relation"]}
                    for e in context.effects[:3]
                ]
                explanation["vulnerable_phases"] = [
                    p["label"] for p in context.vulnerable_phases
                ]
                explanation["recommended_actions"] = [
                    {"label": m["label"], "condition": m.get("condition")}
                    for m in context.mitigations[:2]
                ]
            
            explanations.append(explanation)
        
        return explanations
    
    def _explain_recommendations(self, scenarios, graph_contexts) -> str:
        """Explica por qué se recomiendan ciertas acciones."""
        if not scenarios:
            return "No hay escenarios disponibles."
        
        best = scenarios[0]
        
        # Buscar justificación en el grafo para cada acción
        justifications = []
        for action in best.actions:
            # Buscar en qué contextos aparece esta acción como mitigación
            for risk_type, context in graph_contexts.items():
                for mitigation in context.mitigations:
                    if self._action_matches(action, mitigation):
                        justifications.append(
                            f"- {action.type.capitalize()}: {mitigation.get('condition', 'Recomendado para ' + context.risk_label)}"
                        )
                        break
        
        if justifications:
            return "Justificación de acciones:\n" + "\n".join(justifications)
        return "Acciones basadas en el análisis de riesgos detectados."
    
    def _action_matches(self, action, mitigation: dict) -> bool:
        """Comprueba si una acción del escenario coincide con una mitigación del grafo."""
        action_type = action.type.lower()
        mitigation_id = mitigation.get("id", "").lower()
        
        # Mapeos simples
        mappings = {
            "irrigation": ["riego", "riego_deficitario"],
            "fungicide": ["tratamiento_fungicida"],
            "harvest_timing": ["adelantar_vendimia"],
            "canopy_management": ["deshojado"],
        }
        
        return mitigation_id in mappings.get(action_type, [])
    
    def _generate_sms(self, scenarios, alerts, ccaa) -> str:
        """SMS conciso."""
        if not alerts:
            return f"🍇 {ccaa}: Sin alertas significativas hoy."
        
        risk_text = ", ".join([
            f"{self._risk_emoji(a.risk_type)}{a.level}"
            for a in alerts[:2]
        ])
        
        main_action = "Revisar dashboard"
        if scenarios and scenarios[0].actions:
            main_action = scenarios[0].actions[0].type
        
        sms = f"🍇 {ccaa}\n⚠️ {risk_text}\n✅ {main_action}\n🔗 tudominio.com/d/{ccaa.lower().replace(' ', '')}"
        
        return sms[:160]
    
    def _risk_emoji(self, risk_type: str) -> str:
        emojis = {
            "frost_risk": "🥶",
            "heat_stress": "🌡️",
            "mildiu_risk": "🍄",
            "future_water_stress": "💧",
            "strong_wind_risk": "💨",
        }
        return emojis.get(risk_type, "⚠️")
    
    def _collect_sources(self, graph_contexts) -> List[str]:
        """Recopila todas las fuentes bibliográficas usadas."""
        sources = set()
        for context in graph_contexts.values():
            sources.update(context.sources)
        return sorted(sources)
    
    def _explain_alternatives(self, alternatives) -> List[dict]:
        """Explica brevemente las alternativas."""
        return [
            {
                "actions": [a.type for a in alt.actions],
                "utility": alt.utility,
                "tradeoff": self._describe_tradeoff(alt)
            }
            for alt in alternatives[:2]
        ]
    
    def _describe_tradeoff(self, scenario) -> str:
        """Describe el compromiso de un escenario alternativo."""
        breakdown = scenario.breakdown
        if breakdown.get("cost", 1) > 0.7:
            return "Menor coste pero posiblemente menos efectivo"
        if breakdown.get("sustainability", 1) > 0.8:
            return "Más sostenible pero requiere más seguimiento"
        return "Alternativa viable con diferente balance"
