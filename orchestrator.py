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
        state = self.inference_agent.run(state)
        state = self.prediction_agent.run(state)
        state = self.risk_agent.run(state)
        state = self.deliberative_agent.run(state)
        state = self.explanation_agent.run(state)
        state = self.daily_plan_agent.run(state)
        return state