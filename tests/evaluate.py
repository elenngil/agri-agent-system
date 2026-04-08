"""
Evaluación básica del sistema: compara salidas antes y después de cambios.

Crea un conjunto de casos de prueba con salidas esperadas (manuales)
y mide si el sistema se comporta correctamente.

Ejecutar:
    python tests/evaluate.py
"""

from datetime import date
from models.shared_state import SharedState, WeatherData, CropData, ClimateFeatures, Predictions
from agents.risk_agent import RiskAgent
from agents.deliberative_agent import DeliberativeAgent
from agents.critic_agent import CriticAgent


# ── Casos de evaluación ───────────────────────────────────────────────────────

TEST_CASES = [
    {
        "name": "Helada severa en brotación → debe recomendar cosecha temprana",
        "state_kwargs": {
            "station": "test", "start_date": date(2024, 4, 10),
            "end_date": date(2024, 4, 12), "ccaa": "Castilla y León",
        },
        "weather": WeatherData(-3.0, 12.0, 4.5, 0.0, 40.0, 5.0, 1020.0, 3),
        # corregido: temp_min primero para WeatherData(temp_max, temp_min, ...)
        "expected_risk": "frost_risk",
        "expected_action_type": "harvest_timing",
    },
    {
        "name": "Mildiu alto en floración → debe recomendar fungicida",
        "state_kwargs": {
            "station": "test", "start_date": date(2024, 6, 5),
            "end_date": date(2024, 6, 9), "ccaa": "Galicia",
        },
        "weather": WeatherData(22.0, 14.0, 18.0, 28.0, 92.0, 10.0, 1008.0, 5),
        "expected_risk": "mildiu_risk",
        "expected_action_type": "fungicide",
    },
    {
        "name": "Estrés hídrico en verano → debe recomendar riego",
        "state_kwargs": {
            "station": "test", "start_date": date(2024, 7, 20),
            "end_date": date(2024, 7, 24), "ccaa": "La Rioja",
        },
        "weather": WeatherData(36.0, 18.0, 27.0, 0.0, 28.0, 12.0, 1015.0, 5),
        "expected_risk": "future_water_stress",
        "expected_action_type": "irrigation",
    },
]

CROP = CropData(
    variety="Tempranillo", color="red", water_need="Media",
    frost_sensitivity="Alta", heat_sensitivity="Media", humidity_sensitivity="Alta",
    optimal_temp_min=10.0, optimal_temp_max=30.0,
    optimal_humidity_max=75.0, optimal_precip_mm=400.0,
)


def build_state(case: dict) -> SharedState:
    from tools.climate_features import (
        calculate_etc, calculate_dha, calculate_frost_risk,
        calculate_heat_stress, calculate_mildiu_risk, strong_wind_risk,
    )
    state = SharedState(**case["state_kwargs"])
    state.weather_data = case["weather"]
    state.crop_data = CROP
    state.soil_multiplier = 1.0
    state.climate_features = ClimateFeatures(
        etc=calculate_etc(state.weather_data),
        dha=calculate_dha(state.weather_data),
        frost_risk=calculate_frost_risk(state.weather_data, CROP),
        heat_stress=calculate_heat_stress(state.weather_data, CROP),
        mildiu_risk=calculate_mildiu_risk(state.weather_data),
        strong_wind_risk=strong_wind_risk(state.weather_data),
    )
    state.predictions = Predictions(future_water_stress="Moderado", irrigation_need="Media")
    return state


def run_evaluation():
    passed, failed = 0, 0

    for case in TEST_CASES:
        print(f"\n{'─'*60}")
        print(f"Caso: {case['name']}")

        state = build_state(case)
        state = RiskAgent().run(state)
        state = DeliberativeAgent().run(state, top_n=3)
        critique = CriticAgent().run(state)

        # Verificar riesgo detectado
        risk_types = [a.risk_type for a in state.alerts]
        risk_ok = case["expected_risk"] in risk_types

        # Verificar acción recomendada en el mejor escenario
        best_actions = state.scenarios[0].actions if state.scenarios else []
        action_ok = any(
            a.type == case["expected_action_type"] and a.intensity != "none"
            for a in best_actions
        )

        status = "✓ PASS" if (risk_ok and action_ok) else "✗ FAIL"
        if risk_ok and action_ok:
            passed += 1
        else:
            failed += 1

        print(f"  Riesgo esperado: {case['expected_risk']} → {'✓' if risk_ok else '✗'} (detectados: {risk_types})")
        print(f"  Acción esperada: {case['expected_action_type']} → {'✓' if action_ok else '✗'}")
        print(f"  Crítico: {'aprobado' if critique['approved'] else 'rechazado — ' + critique['reason']}")
        print(f"  {status}")

    print(f"\n{'='*60}")
    print(f"Resultado: {passed}/{passed+failed} casos pasados")
    return failed == 0


if __name__ == "__main__":
    success = run_evaluation()
    exit(0 if success else 1)
