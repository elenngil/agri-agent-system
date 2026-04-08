from itertools import product
from models.shared_state import SharedState, Action, Scenario


class DeliberativeAgent:
    """Genera escenarios de actuación, calcula utilidad y selecciona los mejores."""

    ACTION_SPACE = {
        "irrigation": ["none", "light", "moderate", "intensive"],
        "fungicide": ["none", "preventive", "curative"],
        "harvest_timing": ["normal", "early", "delayed"],
        "canopy_management": ["none", "light_defoliation", "heavy_defoliation"],
    }

    def __init__(self, weights: dict | None = None):
        self.weights = weights or {
            "quality": 0.4,
            "production": 0.35,
            "cost": 0.15,
            "sustainability": 0.10,
        }

    def run(self, state: SharedState, top_n: int = 3, excluded_actions: list[str] | None = None) -> SharedState:
        if state.climate_features is None:
            raise ValueError("climate_features no está disponible en shared_state")
        if state.predictions is None:
            raise ValueError("predictions no está disponible en shared_state")
        if state.crop_data is None:
            raise ValueError("crop_data no está disponible en shared_state")
        candidate_scenarios = self._generate_relevant_scenarios(state)
        # Filtrar acciones problemáticas si el crítico las señaló
        if excluded_actions:
            candidate_scenarios = [
                actions for actions in candidate_scenarios
                if not any(a.type in excluded_actions and a.intensity != "none" for a in actions)
            ]
        scored_scenarios = []
        for actions in candidate_scenarios:
            utility, breakdown = self._calculate_utility(actions, state)
            scored_scenarios.append(Scenario(actions=actions, utility=utility, breakdown=breakdown))
        scored_scenarios.sort(key=lambda s: s.utility, reverse=True)
        state.scenarios = scored_scenarios[:top_n]
        return state

    def _generate_relevant_scenarios(self, state: SharedState) -> list[list[Action]]:
        relevant_actions = {}
        alert_types = {a.risk_type for a in state.alerts}
        climate = state.climate_features
        predictions = state.predictions

        if (
            "future_water_stress" in alert_types
            or "irrigation_need" in alert_types
            or climate.dha > 2
            or predictions.irrigation_need in ("Media", "Alta")
        ):
            relevant_actions["irrigation"] = self.ACTION_SPACE["irrigation"]
        else:
            relevant_actions["irrigation"] = ["none", "light"]

        if "mildiu_risk" in alert_types:
            relevant_actions["fungicide"] = self.ACTION_SPACE["fungicide"]
        else:
            relevant_actions["fungicide"] = ["none"]

        if "frost_risk" in alert_types or "heat_stress" in alert_types:
            relevant_actions["harvest_timing"] = self.ACTION_SPACE["harvest_timing"]
        else:
            relevant_actions["harvest_timing"] = ["normal"]

        if "mildiu_risk" in alert_types or "heat_stress" in alert_types:
            relevant_actions["canopy_management"] = self.ACTION_SPACE["canopy_management"]
        else:
            relevant_actions["canopy_management"] = ["none"]

        keys = list(relevant_actions.keys())
        scenarios = []

        for combo in product(*[relevant_actions[k] for k in keys]):
            actions = [
                Action(
                    type=keys[i],
                    intensity=combo[i],
                    cost=self._action_cost(keys[i], combo[i]),
                )
                for i in range(len(keys))
            ]
            scenarios.append(actions)

        return scenarios

    def _calculate_utility(self, actions: list[Action], state: SharedState) -> tuple[float, dict]:
        breakdown = {}

        breakdown["quality"] = self._estimate_quality_score(actions, state)
        breakdown["production"] = self._estimate_production_score(actions, state)
        breakdown["cost"] = max(0.0, 1 - sum(a.cost for a in actions))
        breakdown["sustainability"] = self._estimate_sustainability_score(actions)

        residual_penalty = self._calculate_residual_penalty(actions, state.alerts)

        utility = (
            self.weights["quality"] * breakdown["quality"]
            + self.weights["production"] * breakdown["production"]
            + self.weights["cost"] * breakdown["cost"]
            + self.weights["sustainability"] * breakdown["sustainability"]
            - residual_penalty
        )

        utility = max(0.0, min(1.0, utility))
        return utility, breakdown

    def _estimate_quality_score(self, actions: list[Action], state: SharedState) -> float:
        score = 0.7
        crop = state.crop_data

        irrigation = self._get_action(actions, "irrigation")
        if irrigation:
            if irrigation.intensity == "light" and crop.color == "red":
                score += 0.08
            elif irrigation.intensity == "moderate":
                score += 0.03
            elif irrigation.intensity == "intensive":
                score -= 0.08

        harvest = self._get_action(actions, "harvest_timing")
        if harvest:
            if harvest.intensity == "early":
                score -= 0.12
            elif harvest.intensity == "delayed":
                score += 0.03

        canopy = self._get_action(actions, "canopy_management")
        if canopy:
            if canopy.intensity == "light_defoliation":
                score += 0.05
            elif canopy.intensity == "heavy_defoliation":
                score -= 0.05

        return max(0.0, min(1.0, score))

    def _estimate_production_score(self, actions: list[Action], state: SharedState) -> float:
        score = 0.75
        alert_types = {a.risk_type for a in state.alerts}

        irrigation = self._get_action(actions, "irrigation")
        fungicide = self._get_action(actions, "fungicide")
        harvest = self._get_action(actions, "harvest_timing")

        if "future_water_stress" in alert_types or "irrigation_need" in alert_types:
            if irrigation and irrigation.intensity in ("moderate", "intensive"):
                score += 0.10
            elif irrigation and irrigation.intensity == "light":
                score += 0.04
            else:
                score -= 0.10

        if "mildiu_risk" in alert_types:
            if fungicide and fungicide.intensity in ("preventive", "curative"):
                score += 0.12
            else:
                score -= 0.15

        if "frost_risk" in alert_types:
            if harvest and harvest.intensity == "early":
                score += 0.06
            else:
                score -= 0.08

        return max(0.0, min(1.0, score))

    def _estimate_sustainability_score(self, actions: list[Action]) -> float:
        score = 0.85

        irrigation = self._get_action(actions, "irrigation")
        fungicide = self._get_action(actions, "fungicide")

        if irrigation:
            if irrigation.intensity == "light":
                score -= 0.03
            elif irrigation.intensity == "moderate":
                score -= 0.08
            elif irrigation.intensity == "intensive":
                score -= 0.18

        if fungicide:
            if fungicide.intensity == "preventive":
                score -= 0.07
            elif fungicide.intensity == "curative":
                score -= 0.12

        return max(0.0, min(1.0, score))

    def _calculate_residual_penalty(self, actions: list[Action], alerts: list) -> float:
        penalty = 0.0

        irrigation = self._get_action(actions, "irrigation")
        fungicide = self._get_action(actions, "fungicide")
        harvest = self._get_action(actions, "harvest_timing")

        for alert in alerts:
            if alert.risk_type in ("future_water_stress", "irrigation_need"):
                if irrigation is None or irrigation.intensity == "none":
                    penalty += alert.penalty
                elif irrigation.intensity == "light":
                    penalty += alert.penalty * 0.5

            elif alert.risk_type == "mildiu_risk":
                if fungicide is None or fungicide.intensity == "none":
                    penalty += alert.penalty
                elif fungicide.intensity == "preventive":
                    penalty += alert.penalty * 0.3

            elif alert.risk_type == "frost_risk":
                if harvest is None or harvest.intensity == "normal":
                    penalty += alert.penalty
                elif harvest.intensity == "early":
                    penalty += alert.penalty * 0.4

            else:
                penalty += alert.penalty * 0.3

        return min(1.0, penalty)

    def _action_cost(self, action_type: str, intensity: str) -> float:
        cost_map = {
            "irrigation": {
                "none": 0.0,
                "light": 0.05,
                "moderate": 0.10,
                "intensive": 0.20,
            },
            "fungicide": {
                "none": 0.0,
                "preventive": 0.08,
                "curative": 0.14,
            },
            "harvest_timing": {
                "normal": 0.0,
                "early": 0.06,
                "delayed": 0.05,
            },
            "canopy_management": {
                "none": 0.0,
                "light_defoliation": 0.05,
                "heavy_defoliation": 0.10,
            },
        }
        return cost_map.get(action_type, {}).get(intensity, 0.0)

    def _get_action(self, actions: list[Action], action_type: str) -> Action | None:
        return next((a for a in actions if a.type == action_type), None)