import logging
import time
from models.shared_state import SharedState, RiskLevel
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

    def __init__(self, model, deliberative_weights: dict | None = None):
        self.observation   = ObservationAgent()
        self.inference     = InferenceAgent()
        self.prediction    = PredictionAgent()
        self.risk          = RiskAgent()
        self.deliberative = DeliberativeAgent(weights=deliberative_weights)
        self.explanation   = ExplanationAgent(llm_client=model)
        self.daily_plan    = DailyPlanAgent()
        self.writer        = OutputWriter()
        self.critic        = CriticAgent()

    def run(self, state: SharedState) -> SharedState:

        t0 = time.perf_counter()
        state = self.observation.run(state)
        logger.info("Observación completada en %.3fs", time.perf_counter() - t0)

        if state.weather_data is None:
            logger.warning("Sin datos meteorológicos — abortando pipeline")
            return state

        t0 = time.perf_counter()
        state = self.inference.run(state)
        logger.info("Inferencia completada en %.3fs", time.perf_counter() - t0)

        t0 = time.perf_counter()
        state = self.prediction.run(state)
        logger.info("Predicción completada en %.3fs", time.perf_counter() - t0)

        t0 = time.perf_counter()
        state = self.risk.run(state)
        logger.info("Riesgos evaluados en %.3fs — %d alertas generadas", time.perf_counter() - t0, len(state.alerts))

        t_total = time.perf_counter()

        critical_alerts = [
            a for a in state.alerts
            if a.level == RiskLevel.CRITICAL
        ]

        if critical_alerts:
            logger.info(f"{len(critical_alerts)} alerta(s) crítica(s) — activando ruta urgente")
            state = self._run_urgent_path(state)
        else:
            logger.info("Sin alertas críticas — ruta estándar")
            state = self._run_standard_path(state)

        t0 = time.perf_counter()
        state = self.daily_plan.run(state)
        logger.info("Plan diario generado en %.3fs", time.perf_counter() - t0)

        logger.info("Pipeline completado en %.3fs", time.perf_counter() - t_total)

        self.writer.write(state)
        return state

    def _run_urgent_path(self, state: SharedState) -> SharedState:
        """
        Ruta cuando hay alertas críticas.
        Prioriza la rapidez (top_n=1, sin deliberación amplia), pero los
        guardarraíles agronómicos no-negociables (HARD_RULES) se validan
        igualmente mediante el CriticAgent. La urgencia sacrifica la
        deliberación, nunca la inocuidad de la acción recomendada.
        """
        MAX_RETRIES = 2
        excluded: list[tuple[str, str]] = []
        for attempt in range(MAX_RETRIES):
            state = self.deliberative.run(state, top_n=1, excluded_actions=excluded or None, urgent=True)
            critique = self.critic.run(state)
            if critique["approved"]:
                logger.info("Deliberación rápida validada por el crítico (intento %d)", attempt + 1)
                break
            excluded = critique.get("problematic_actions", [])
            logger.warning("Ruta urgente — intento %d vetado por guardarraíl: %s", attempt + 1, critique["reason"])
        else:
            logger.error("Crítico no aprobó la ruta urgente tras %d intentos — usando último resultado seguro disponible", MAX_RETRIES)

        state = self.explanation.run(state)
        logger.info("Explicación urgente generada")

        return state

    def _run_standard_path(self, state: SharedState) -> SharedState:
        """
        Ruta estándar: deliberación completa + crítico + explicación.
        """

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
            logger.error("Crítico no aprobó tras %d intentos — usando último resultado", MAX_RETRIES)

        state = self.explanation.run(state)
        logger.info("Explicación generada")

        return state