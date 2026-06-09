from typing import List
from models.shared_state import SharedState, RiskLevel
from rag.graph.graph_retriever import get_graph_retriever, GraphContext
from smolagents import ChatMessage
import os


class ExplanationAgent:

    def __init__(self, llm_client):
        self.llm = llm_client
        self.graph_retriever = get_graph_retriever()

    def run(self, state: SharedState) -> SharedState:
        scenarios = state.scenarios or []
        alerts    = state.alerts    or []

        graph_contexts = self._get_graph_contexts(alerts)

        explanation = {
            "summary":                  self._generate_summary(scenarios, alerts, graph_contexts, state.ccaa),
            "risk_explanation":         self._explain_risks(alerts, graph_contexts),
            "recommendation_reasoning": self._explain_recommendations(scenarios, alerts, graph_contexts, state.ccaa),
            "alternatives":             self._explain_alternatives(scenarios[1:] if len(scenarios) > 1 else []),
            "sms_text":                 self._generate_sms(scenarios, alerts, state.ccaa),
            "sources":                  self._collect_sources(graph_contexts),
        }

        state.explanation = explanation
        return state


    def _level_to_text(self, level) -> str:
        return level.value if isinstance(level, RiskLevel) else str(level)

    def _get_graph_contexts(self, alerts: List) -> dict[str, GraphContext]:
        contexts = {}
        for alert in alerts:
            if alert.risk_type not in contexts:
                ctx = self.graph_retriever.get_context_for_risk(alert.risk_type)
                if ctx:
                    contexts[alert.risk_type] = ctx
        return contexts

    def _call_llm(self, prompt: str, fallback: str) -> str:
        try:
            response = self.llm([ChatMessage(role="user", content=prompt)])
            return response.content if hasattr(response, "content") else str(response)
        except Exception:
            return fallback


    def _generate_summary(self, scenarios, alerts, graph_contexts, ccaa) -> str:
        graph_info = "\n\n".join(
            ctx.to_prompt_context() for ctx in graph_contexts.values()
        )
        recommended_actions = "ninguna accion urgente"
        if scenarios and scenarios[0].actions:
            recommended_actions = ", ".join(
                f"{a.type.replace('_',' ')} ({a.intensity})"
                for a in scenarios[0].actions
                if a.intensity != "none"
            ) or "mantener seguimiento rutinario"

        risks_text = ", ".join(
            f"{a.risk_type.replace('_',' ')} nivel {self._level_to_text(a.level)}"
            for a in alerts
        ) or "sin riesgos destacados"

        prompt = f"""Eres un asesor viticola experto. Genera un resumen de 2-3 frases para un viticultor en {ccaa}.

CONOCIMIENTO ESTRUCTURADO:
{graph_info if graph_info else "Sin riesgos activos en el grafo."}

SITUACION ACTUAL:
- Region: {ccaa}
- Riesgos detectados: {risks_text}
- Acciones recomendadas: {recommended_actions}

INSTRUCCIONES:
- Sé directo y practico. Sin tecnicismos innecesarios.
- Menciona la accion principal recomendada.
- Si no hay riesgos, indícalo claramente.
- No uses emojis ni guiones.
- Maximo 3 frases."""

        return self._call_llm(prompt, f"En {ccaa}, se recomienda revisar las condiciones del cultivo.")

    def _explain_recommendations(self, scenarios, alerts, graph_contexts, ccaa) -> str:
        if not scenarios:
            return "No hay escenarios evaluados disponibles."

        best = scenarios[0]
        actions_text = "\n".join(
            f"- {a.type.replace('_',' ').capitalize()}: {a.intensity}"
            for a in best.actions
            if a.intensity != "none"
        ) or "- Ninguna accion urgente recomendada"

        graph_info = "\n\n".join(
            ctx.to_prompt_context() for ctx in graph_contexts.values()
        )

        breakdown = best.breakdown or {}
        scores_text = ", ".join(
            f"{k}={v:.2f}" for k, v in breakdown.items()
        ) if breakdown else "no disponible"

        risks_text = ", ".join(
            f"{a.risk_type.replace('_',' ')} ({self._level_to_text(a.level)})"
            for a in alerts
        ) or "ninguno"

        prompt = f"""Eres un asesor viticola experto. Justifica en 3-4 frases por que se han recomendado estas acciones.

ACCIONES RECOMENDADAS:
{actions_text}

RIESGOS DETECTADOS:
{risks_text}

CONOCIMIENTO AGRONOMICO:
{graph_info if graph_info else "Sin contexto de grafo disponible."}

SCORES DE LA DECISION (calidad, produccion, coste, sostenibilidad):
{scores_text}

INSTRUCCIONES:
- Explica por que cada accion principal es adecuada para los riesgos detectados.
- Usa el conocimiento agronomico para fundamentar la justificacion.
- Menciona el equilibrio entre calidad, produccion y sostenibilidad.
- Sin emojis ni guiones al inicio de frases.
- Maximo 4 frases."""

        return self._call_llm(
            prompt,
            "La recomendacion ha sido seleccionada por maximizar la utilidad agronómica considerando los riesgos activos."
        )


    def _explain_risks(self, alerts, graph_contexts) -> list:
        '''
        
        '''
        result = []
        for alert in alerts[:3]:
            ctx = graph_contexts.get(alert.risk_type)
            entry = {
                "type":      alert.risk_type,
                "level":     self._level_to_text(alert.level),
                "value":     alert.value,
                "threshold": alert.threshold,
            }
            if ctx:
                entry["description"]         = getattr(ctx, "description", "")
                entry["causes"]              = getattr(ctx, "causes", [])
                entry["effects"]             = getattr(ctx, "effects", [])
                entry["recommended_actions"] = getattr(ctx, "mitigations", [])
                entry["vulnerable_phases"]   = getattr(ctx, "vulnerable_phases", [])
            result.append(entry)
        return result


    TRADUCCION_SMS = {
        "irrigation": "riego", "fungicide": "fungicida",
        "harvest_timing": "vendimia", "canopy_management": "deshojado",
        "none": "ninguno", "light": "ligero", "moderate": "moderado",
        "intensive": "intensivo", "preventive": "preventivo",
        "curative": "curativo", "early": "anticipado",
        "delayed": "retrasado", "normal": "normal",
        "heavy_defoliation": "deshojado intenso",
        "light_defoliation": "deshojado ligero",
        "future_water_stress": "estres hidrico",
        "mildiu_risk": "riesgo mildiu",
        "frost_risk": "riesgo helada",
        "heat_stress": "estres termico",
        "strong_wind_risk": "viento fuerte",
        "irrigation_need": "necesidad riego",
    }

    def _generate_sms(self, scenarios, alerts, ccaa) -> str:
        if not alerts:
            return f"AgroVid | {ccaa} | Sin alertas activas. Condiciones favorables para el vinedo. Mantener seguimiento rutinario."

        main_alert = alerts[0]
        level_text = self._level_to_text(main_alert.level).upper()
        risk_text  = self.TRADUCCION_SMS.get(
            main_alert.risk_type,
            main_alert.risk_type.replace("_", " ")
        ).capitalize()

        valor_text = ""
        if getattr(main_alert, "value", None) is not None:
            valor_text = f" ({main_alert.value})"

        action_text = ""
        if scenarios and scenarios[0].actions:
            main_action = next(
                (a for a in scenarios[0].actions if a.intensity != "none"), None
            )
            if main_action:
                tipo       = self.TRADUCCION_SMS.get(main_action.type, main_action.type)
                intensidad = self.TRADUCCION_SMS.get(main_action.intensity, main_action.intensity)
                action_text = f" Accion: {tipo} {intensidad}."

        base = f"AgroVid | {ccaa} | Alerta: {risk_text} nivel {level_text}{valor_text}.{action_text}"

        if len(base) <= 157:
            base += " Revisa el detalle en la app."

        return base[:160]


    def _explain_alternatives(self, alternatives) -> list:
        result = []
        for i, scenario in enumerate(alternatives[:2]):
            actions = [
                f"{a.type.replace('_',' ')} {a.intensity}"
                for a in scenario.actions
                if a.intensity != "none"
            ]
            result.append({
                "utility":  round(scenario.utility, 3),
                "actions":  actions,
                "tradeoff": f"Alternativa {i+2} con utilidad {scenario.utility:.2f}.",
            })
        return result

    def _collect_sources(self, graph_contexts) -> list:
        sources = set()
        for c in graph_contexts.values():
            sources.update(c.sources)
        return list(sources)