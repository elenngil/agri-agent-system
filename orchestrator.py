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


class Orchestrator:
    """
    Ejecuta el pipeline completo de agentes en orden.
    Cada agente recibe el estado compartido, lo enriquece y lo devuelve.
    Además, guarda la salida final para que pueda ser consumida por el dashboard.
    """

    def __init__(self, model):
        self.observation_agent = ObservationAgent()
        self.inference_agent = InferenceAgent()
        self.prediction_agent = PredictionAgent()
        self.risk_agent = RiskAgent()
        self.deliberative_agent = DeliberativeAgent()
        self.explanation_agent = ExplanationAgent(model=model)
        self.daily_plan_agent = DailyPlanAgent()

    def run(self, state: SharedState) -> SharedState:
        state = self.observation_agent.run(state)
        print("✓ Observación completada")

        state = self.inference_agent.run(state)
        print("✓ Inferencia completada")

        state = self.prediction_agent.run(state)
        print("✓ Predicción completada")

        state = self.risk_agent.run(state)
        print("✓ Evaluación de riesgos completada")

        state = self.deliberative_agent.run(state)
        print("✓ Deliberación completada")

        # Explicación global del sistema
        state = self.explanation_agent.run(state)
        print("✓ Explicación generada")

        # Plan diario operativo final
        state = self.daily_plan_agent.run(state)
        print("✓ Plan diario generado")

        # Guardar salida para el dashboard
        self._save_output(state)

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
                if getattr(state, "crop_data", None)
                else "desconocida",
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
                    {
                        "risk": p.risk,
                        "label": p.label,
                        "priority": p.priority,
                        "action": p.action,
                    }
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