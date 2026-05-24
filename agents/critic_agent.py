from models.shared_state import SharedState, RiskLevel


HARD_RULES = [
    {
        "id": "no_fungicide_in_harvest",
        "description": "No recomendar fungicida curativo en fase de maduracion tardia",
        "check": lambda actions, state: not (
            any(a.type == "fungicide" and a.intensity == "curative" for a in actions)
            and getattr(state.crop_data, "variety", "") in ("Tempranillo", "Garnacha")
            and hasattr(state, "start_date")
            and getattr(state.start_date, "month", 0) >= 9
        ),
        "problematic_actions": [("fungicide", "curative")],
    },
    {
        "id": "no_heavy_defoliation_in_heat",
        "description": "No recomendar defoliacion intensa si hay estres termico alto",
        "check": lambda actions, state: not (
            any(a.type == "canopy_management" and a.intensity == "heavy_defoliation" for a in actions)
            and state.climate_features is not None
            and state.climate_features.heat_stress is not None
            and state.climate_features.heat_stress.get("level", "").lower() in (
                RiskLevel.HIGH.value.lower(), RiskLevel.CRITICAL.value.lower()
            )
        ),
        "problematic_actions": [("canopy_management", "heavy_defoliation")],
    },
    {
        "id": "no_intensive_irrigation_with_rain",
        "description": "No recomendar riego intensivo si la precipitacion supera 30mm",
        "check": lambda actions, state: not (
            any(a.type == "irrigation" and a.intensity == "intensive" for a in actions)
            and state.weather_data is not None
            and state.weather_data.precipitation is not None
            and state.weather_data.precipitation > 30
        ),
        "problematic_actions": [("irrigation", "intensive")],
    },
]


class CriticAgent:
    
    def run(self, state: SharedState) -> dict:
        if not state.scenarios:
            return {
                "approved": True,
                "reason": "Sin escenarios que verificar",
                "problematic_actions": [],
            }

        actions = state.scenarios[0].actions

        for rule in HARD_RULES:
            try:
                if not rule["check"](actions, state):
                    return {
                        "approved":            False,
                        "reason":              rule["description"],
                        "problematic_actions": rule["problematic_actions"],
                        "rule_id":             rule["id"],
                    }
            except Exception:
                # Si la regla falla por datos incompletos no bloqueamos
                continue

        return {
            "approved":            True,
            "reason":              "Todas las reglas agronomicas verificadas correctamente",
            "problematic_actions": [],
        }