# orchestrator.py — reemplazar completamente

import json
from pathlib import Path

from models.shared_state import SharedState
from agents.observation_agent import ObservationAgent
from agents.inference_agent import InferenceAgent
from agents.prediction_agent import PredictionAgent
from agents.risk_agent import RiskAgent
from agents.deliberative_agent import DeliberativeAgent
from agents.explanation_agent import ExplanationAgent
from agents.daily_plan_agent import DailyPlanAgent
from agents.critic_agent import CriticAgent


class Orchestrator:
    """
    Supervisor que decide qué agentes ejecutar y en qué orden
    según el estado del sistema. No es un pipeline fijo.
    """

    def __init__(self, model):
        self.observation   = ObservationAgent()
        self.inference     = InferenceAgent()
        self.prediction    = PredictionAgent()
        self.risk          = RiskAgent()
        self.deliberative  = DeliberativeAgent()
        self.explanation   = ExplanationAgent(llm_client=model)
        self.daily_plan    = DailyPlanAgent()
        self.critic        = CriticAgent()

    def run(self, state: SharedState) -> SharedState:
        # ── Fase 1: siempre se ejecuta ──────────────────────────
        state = self.observation.run(state)
        print("✓ Observación completada")

        if state.weather_data is None:
            print("⚠ Sin datos meteorológicos — abortando pipeline")
            return state

        state = self.inference.run(state)
        print("✓ Inferencia completada")

        state = self.prediction.run(state)
        print("✓ Predicción completada")

        state = self.risk.run(state)
        print("✓ Riesgos evaluados")

        # ── Fase 2: routing según nivel de riesgo ───────────────
        critical_alerts = [a for a in state.alerts if a.level in ("alto", "crítico")]

        if critical_alerts:
            print(f"⚡ {len(critical_alerts)} alerta(s) crítica(s) — activando ruta urgente")
            state = self._run_urgent_path(state)
        else:
            print("🟢 Sin alertas críticas — ruta estándar")
            state = self._run_standard_path(state)

        # ── Fase 3: plan diario siempre ─────────────────────────
        state = self.daily_plan.run(state)
        print("✓ Plan diario generado")

        self._save_output(state)
        return state

    def _run_urgent_path(self, state: SharedState) -> SharedState:
        """
        Ruta cuando hay alertas críticas.
        Prioriza explicación inmediata sin deliberación completa.
        """
        # Deliberación rápida con top_n reducido
        state = self.deliberative.run(state, top_n=1)
        print("✓ Deliberación rápida completada")

        # Explicación directa sin pasar por crítico
        # (en alertas críticas queremos velocidad)
        state = self.explanation.run(state)
        print("✓ Explicación urgente generada")

        return state

    def _run_standard_path(self, state: SharedState) -> SharedState:
        """
        Ruta estándar: deliberación completa + crítico + explicación.
        """
        state = self.deliberative.run(state, top_n=3)
        print("✓ Deliberación completa")

        # El crítico verifica que la recomendación tiene sentido
        critique = self.critic.run(state)
        if not critique["approved"]:
            print(f"⚠ Crítico rechazó recomendación: {critique['reason']}")
            # Reintentar deliberación con restricción adicional
            state = self.deliberative.run(state, top_n=3, excluded_actions=critique.get("problematic_actions", []))
            print("✓ Deliberación corregida")

        state = self.explanation.run(state)
        print("✓ Explicación generada")

        return state

    def _save_output(self, state: SharedState) -> None:
        Path("output").mkdir(exist_ok=True)

        plan = getattr(state, "daily_plan", None)
        explanation = getattr(state, "explanation", None) or {}

        data = {
            "meta": {
                "region": getattr(state, "ccaa", "—"),
                "station": getattr(state, "station", "—"),
                "start_date": str(getattr(state, "start_date", "")),
                "end_date": str(getattr(state, "end_date", "")),
                "variety": getattr(state.crop_data, "variety", "desconocida")
                if getattr(state, "crop_data", None) else "desconocida",
                "dashboard_url": "http://localhost:8501",
            },
            "sms": plan.sms if plan else "—",
            "daily_plan": {
                "irrigation": {
                    "base_liters": plan.irrigation.base_liters,
                    "adjusted_liters": plan.irrigation.adjusted_liters,
                    "adjustment_reason": plan.irrigation.adjustment_reason,
                    "soil_multiplier": plan.irrigation.soil_multiplier,
                    "assumed_values": plan.irrigation.assumed_values,
                },
                "climate": {
                    "condition": plan.climate.condition,
                    "temp_min": plan.climate.temp_min,
                    "temp_max": plan.climate.temp_max,
                    "precipitation": plan.climate.precipitation,
                    "humidity": plan.climate.humidity,
                    "interpretation": plan.climate.interpretation,
                },
                "crop_status": {
                    "phase": plan.crop_status.phase,
                    "recommendation": plan.crop_status.recommendation,
                    "assumed": plan.crop_status.assumed,
                },
                "prevention": [
                    {"risk": p.risk, "label": p.label, "priority": p.priority, "action": p.action}
                    for p in plan.prevention
                ],
                "explanation": plan.explanation,
            } if plan else {},
            "explanation_agent": {
                "summary": explanation.get("summary", ""),
                "confidence": explanation.get("confidence", {}),
                "sms_text": explanation.get("sms_text", ""),
                "risk_explanation": explanation.get("risk_explanation", []),
                "alternatives": explanation.get("alternatives", []),
            },
        }

        with open("output/daily_plan.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("✅ Output guardado en output/daily_plan.json")
