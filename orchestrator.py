# orchestrator.py — reemplazar completamente

import json
from pathlib import Path
import logging
from models.shared_state import SharedState
from agents.observation_agent import ObservationAgent
from agents.inference_agent import InferenceAgent
from agents.prediction_agent import PredictionAgent
from agents.risk_agent import RiskAgent
from agents.deliberative_agent import DeliberativeAgent
from agents.explanation_agent import ExplanationAgent
from agents.daily_plan_agent import DailyPlanAgent
from agents.critic_agent import CriticAgent

from output.writer import OutputWriter

logger = logging.getLogger(__name__)

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
        self.writer        = OutputWriter()
        self.critic        = CriticAgent()

    def run(self, state: SharedState) -> SharedState:
        # ── Fase 1: siempre se ejecuta ──────────────────────────
        state = self.observation.run(state)
        logger.info("Observación completada")

        if state.weather_data is None:
            logger.warning("Sin datos meteorológicos — abortando pipeline")
            return state

        state = self.inference.run(state)
        logger.info("Inferencia completada")

        state = self.prediction.run(state)
        logger.info("Predicción completada")

        state = self.risk.run(state)
        logger.info("Riesgos evaluados")

        # ── Fase 2: routing según nivel de riesgo ───────────────
        critical_alerts = [a for a in state.alerts if a.level in ("alto", "crítico")]

        if critical_alerts:
            logger.info(f"{len(critical_alerts)} alerta(s) crítica(s) — activando ruta urgente")
            state = self._run_urgent_path(state)
        else:
            logger.info("Sin alertas críticas — ruta estándar")
            state = self._run_standard_path(state)

        # ── Fase 3: plan diario siempre ─────────────────────────
        state = self.daily_plan.run(state)
        logger.info("Plan diario generado")

        self.writer.write(state)
        return state

    def _run_urgent_path(self, state: SharedState) -> SharedState:
        """
        Ruta cuando hay alertas críticas.
        Prioriza explicación inmediata sin deliberación completa.
        """
        # Deliberación rápida con top_n reducido
        state = self.deliberative.run(state, top_n=1)
        logger.info("Deliberación rápida completada")

        # Explicación directa sin pasar por crítico
        # (en alertas críticas queremos velocidad)
        state = self.explanation.run(state)
        logger.info("Explicación urgente generada")

        return state

    def _run_standard_path(self, state: SharedState) -> SharedState:
        """
        Ruta estándar: deliberación completa + crítico + explicación.
        """
        
        # El crítico verifica que la recomendación tiene sentido
        MAX_RETRIES = 2
        excluded: list[str] = []
        for attempt in range(MAX_RETRIES):
            state = self.deliberative.run(state, top_n=3, excluded_actions=excluded or None)
            critique = self.critic.run(state)
            if critique["approved"]:
                logger.info("Deliberación aprobada (intento %d)", attempt + 1)
                break
            excluded = critique.get("problematic_actions", [])
            logger.warning("Intento %d rechazado: %s", attempt + 1, critique["reason"])
        else:
            # Se agotaron los reintentos — acepta el último resultado con aviso
            logger.error("Crítico no aprobó tras %d intentos — usando último resultado", MAX_RETRIES)

        state = self.explanation.run(state)
        logger.info("Explicación generada")

        return state

