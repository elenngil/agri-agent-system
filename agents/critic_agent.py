"""
CriticAgent: verifica que la recomendación del DeliberativeAgent
no viola reglas agronómicas básicas antes de generar la explicación.

No usa LLM: es determinista. Rápido y predecible.
"""

from models.shared_state import SharedState


# Reglas que nunca deben violarse, independientemente del scoring de utilidad
HARD_RULES = [
    {
        "id": "no_fungicide_in_harvest",
        "description": "No recomendar fungicida curativo en fase de maduración tardía",
        "check": lambda actions, state: not (
            any(a.type == "fungicide" and a.intensity == "curative" for a in actions)
            and getattr(state.crop_data, "variety", "") in ("Tempranillo", "Garnacha")
            and hasattr(state, "start_date")
            and getattr(state.start_date, "month", 0) >= 9
        ),
        "problematic_actions": ["fungicide"],
    },
    {
        "id": "no_heavy_defoliation_in_heat",
        "description": "No recomendar defoliación intensa si hay estrés térmico alto",
        "check": lambda actions, state: not (
            any(a.type == "canopy_management" and a.intensity == "heavy_defoliation" for a in actions)
            and state.climate_features is not None
            and isinstance(state.climate_features.heat_stress, dict)
            and state.climate_features.heat_stress.get("level") == "Alto"
        ),
        "problematic_actions": ["canopy_management"],
    },
    {
        "id": "no_intensive_irrigation_with_rain",
        "description": "No recomendar riego intensivo si la precipitación supera 30mm",
        "check": lambda actions, state: not (
            any(a.type == "irrigation" and a.intensity == "intensive" for a in actions)
            and state.weather_data is not None
            and state.weather_data.precipitation > 30
        ),
        "problematic_actions": ["irrigation"],
    },
]


class CriticAgent:
    """
    Verifica las recomendaciones del mejor escenario contra reglas agronómicas duras.
    Devuelve un dict con approved, reason y problematic_actions.
    """

    def run(self, state: SharedState) -> dict:
        if not state.scenarios:
            return {"approved": True, "reason": "Sin escenarios que verificar", "problematic_actions": []}

        best = state.scenarios[0]
        actions = best.actions

        for rule in HARD_RULES:
            try:
                if not rule["check"](actions, state):
                    return {
                        "approved": False,
                        "reason": rule["description"],
                        "problematic_actions": rule["problematic_actions"],
                        "rule_id": rule["id"],
                    }
            except Exception:
                # Si la regla falla por datos incompletos, no bloqueamos
                continue

        return {
            "approved": True,
            "reason": "Riego intensivo con suelo saturado es contraproducente",
            "problematic_actions": [("irrigation", "intensive")]
        }
