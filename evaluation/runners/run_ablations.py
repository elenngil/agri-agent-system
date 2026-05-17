"""
run_ablations.py
----------------
Ejecuta 6 estudios de ablacion por capas sobre los 15 escenarios.

Ablaciones implementadas:
  A0 - completo          Sistema completo (referencia)
  A1 - sin_fase1         WeatherData por defecto, sin AEMET
  A2 - sin_inference     ETc=0, DHA=0 — sin InferenceAgent
  A3 - sin_prediction    future_water_stress=Bajo siempre — sin PredictionAgent
  A4 - sin_routing       Siempre ruta estandar, top_n=3 fijo
  A5 - sin_critic        Sin guardarrailes agronómicos
  A6 - sin_rag           Sin grafo de conocimiento

Uso:
    python -m evaluation.runners.run_ablations --skip-llm
"""

import csv
import sys
import traceback
from copy import deepcopy
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.shared_state import SharedState, RiskLevel, ClimateFeatures, Predictions, WeatherData
from agents.inference_agent import InferenceAgent
from agents.prediction_agent import PredictionAgent
from agents.risk_agent import RiskAgent
from agents.deliberative_agent import DeliberativeAgent
from agents.critic_agent import CriticAgent
from agents.daily_plan_agent import DailyPlanAgent

from evaluation.scenarios.test_scenarios import SCENARIOS, TEMPRANILLO
from evaluation.runners.run_pipeline import build_state_from_scenario, check_ground_truth

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

CONFIGS = ["completo", "sin_fase1", "sin_inference", "sin_prediction",
           "sin_routing", "sin_critic", "sin_rag"]

# WeatherData neutral para A1 — condiciones promedio sin riesgo
WEATHER_DEFAULT = WeatherData(
    temperature_max=22.0,
    temperature_min=12.0,
    temperature_mean=17.0,
    precipitation=5.0,
    humidity=60.0,
    wind=10.0,
    pressure=1013.0,
    days_count=5,
)


def run_ablation(scenario: dict, config: str, skip_llm: bool = False) -> dict:
    """
    Ejecuta un escenario con una configuracion de ablacion.
    Cada config degrada una capa distinta del sistema.
    """
    fila = {
        "timestamp":   datetime.now().isoformat(),
        "scenario_id": scenario["id"],
        "scenario":    scenario["name"][:40],
        "config":      config,
    }

    try:
        # ── Construccion del estado base ─────────────────────────────────────

        if config == "sin_fase1":
            # A1: sustituir datos reales de AEMET por WeatherData neutral
            # Mide: cuanto aportan los datos reales frente a valores por defecto
            state = SharedState(
                station=scenario["station"],
                start_date=scenario["start_date"],
                end_date=scenario["end_date"],
                ccaa=scenario["ccaa"],
            )
            state.crop_data       = scenario["crop"]
            state.soil_multiplier = 1.0
            state.weather_data    = WEATHER_DEFAULT  # datos neutrales, sin AEMET
        else:
            state = build_state_from_scenario(scenario)

        # ── Fase 1: InferenceAgent ────────────────────────────────────────────

        if config == "sin_inference":
            # A2: saltar InferenceAgent, poner ETc=0 y DHA=0
            # Mide: cuanto aportan los indicadores derivados (ETc, DHA)
            # Sin ETc ni DHA, el DeliberativeAgent no detecta estres hidrico
            state.climate_features = ClimateFeatures(
                etc=0.0,
                dha=0.0,
                frost_risk={"level": "Nulo",  "score": 0.0, "value": 0.0, "threshold": 0.0},
                heat_stress={"level": "Bajo",  "score": 0.0, "value": 0.0, "threshold": 0.0},
                mildiu_risk={"level": "Bajo",  "score": 0.0, "value": 0.0, "threshold": 0.0},
                strong_wind_risk={"level": "Bajo", "score": 0.0, "value": 0.0, "threshold": 0.0},
            )
        else:
            state = InferenceAgent().run(state)

        # ── Fase 1: PredictionAgent ───────────────────────────────────────────

        if config == "sin_prediction":
            # A3: saltar PredictionAgent, asumir siempre estres bajo
            # Mide: cuanto aporta predecir el futuro
            # Sin prediccion, el sistema nunca recomienda riego preventivo
            state.predictions = Predictions(
                future_water_stress="Bajo",
                irrigation_need="Baja",
            )
        else:
            state = PredictionAgent().run(state)

        # ── Fase 1: RiskAgent ─────────────────────────────────────────────────
        state = RiskAgent().run(state)

        # ── Fase 2: routing ───────────────────────────────────────────────────

        critical = [a for a in state.alerts
                    if a.level in (RiskLevel.HIGH, RiskLevel.CRITICAL)]

        if config == "sin_routing":
            # A4: ignorar el routing, siempre ruta estandar con top_n=3
            # Mide: cuanto aporta el routing condicional
            # Sin routing, los casos urgentes no priorizan velocidad
            ruta  = "estandar_forzado"
            top_n = 3
        else:
            ruta  = "urgente" if critical else "estandar"
            top_n = 1 if ruta == "urgente" else 3

        state = DeliberativeAgent().run(state, top_n=top_n)

        # ── Fase 2: CriticAgent ───────────────────────────────────────────────

        critic_rechazos = 0
        violaciones     = 0

        if config == "sin_critic":
            # A5: no ejecutar CriticAgent — medir violaciones que ocurren
            critique = CriticAgent().run(state)
            if not critique["approved"]:
                violaciones += 1
            # No corregimos: la recomendacion incorrecta llega al agricultor

        elif config not in ("sin_routing",) or ruta == "estandar_forzado":
            # CriticAgent activo en ruta estandar (o siempre si sin_routing)
            if ruta in ("estandar", "estandar_forzado"):
                critique = CriticAgent().run(state)
                if not critique["approved"]:
                    critic_rechazos += 1
                    excluded = critique.get("problematic_actions", [])
                    state = DeliberativeAgent().run(
                        state, top_n=3, excluded_actions=excluded or None
                    )

        # ── ExplanationAgent (opcional) ───────────────────────────────────────

        if not skip_llm:
            try:
                import os
                from dotenv import load_dotenv
                from smolagents import InferenceClientModel
                from agents.explanation_agent import ExplanationAgent
                load_dotenv()
                model = InferenceClientModel(
                    model_id="Qwen/Qwen2.5-72B-Instruct",
                    token=os.environ["HF_TOKEN"],
                )

                if config == "sin_rag":
                    # A6: sin grafo de conocimiento
                    agent = ExplanationAgent(llm_client=model)
                    agent.graph_retriever = None
                    state = agent.run(state)
                else:
                    state = ExplanationAgent(llm_client=model).run(state)

            except Exception as e:
                fila["explanation_error"] = str(e)

        # ── DailyPlanAgent ────────────────────────────────────────────────────
        state = DailyPlanAgent().run(state)
        gt    = check_ground_truth(state, scenario)

        fila.update({
            "ruta":            ruta,
            "n_alertas":       len(state.alerts),
            "utilidad":        round(state.scenarios[0].utility, 4) if state.scenarios else 0.0,
            "critic_rechazos": critic_rechazos,
            "violaciones":     violaciones,
            "exito":           state.daily_plan is not None,
            **gt,
        })

    except Exception as e:
        fila.update({
            "exito":   False,
            "gt_pass": False,
            "errores": traceback.format_exc()[:300],
        })
        print(f"\n    ERROR: {e}")

    return fila


def run_all_ablations(skip_llm: bool = False) -> None:
    filas = []
    total = len(SCENARIOS) * len(CONFIGS)
    completadas = 0

    for config in CONFIGS:
        print(f"\n{'='*55}")
        print(f"ABLACION: {config}")
        print(f"{'='*55}")

        for scenario in SCENARIOS:
            completadas += 1
            print(f"  [{completadas}/{total}] {scenario['id']}", end=" ")

            fila = run_ablation(scenario, config, skip_llm=skip_llm)
            filas.append(fila)

            status = "✓" if fila.get("gt_pass") else "✗"
            util   = fila.get("utilidad", "—")
            viols  = fila.get("violaciones", 0)
            print(f"-> {status} utilidad={util} violaciones={viols}")

    output_path = RESULTS_DIR / "ablation_results.csv"
    if filas:
        campos = list(filas[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(filas)

    print(f"\nResultados guardados en {output_path}")
    _print_summary(filas)


def _print_summary(filas: list[dict]) -> None:
    import statistics

    print("\n" + "="*65)
    print("RESUMEN ABLACIONES POR CAPAS")
    print(f"{'Config':<22} {'GT Pass':>8} {'Utilidad':>10} {'Violaciones':>12} {'Alertas':>8}")
    print("-"*65)

    for config in CONFIGS:
        subset  = [f for f in filas if f.get("config") == config]
        gt_pass = sum(1 for f in subset if f.get("gt_pass"))
        utils   = [f["utilidad"] for f in subset if "utilidad" in f and f["utilidad"] > 0]
        viols   = sum(f.get("violaciones", 0) for f in subset)
        alertas = [f["n_alertas"] for f in subset if "n_alertas" in f]

        util_media    = statistics.mean(utils)   if utils   else 0
        alertas_media = statistics.mean(alertas) if alertas else 0

        print(f"{config:<22} {gt_pass:>4}/{len(subset):<4} "
              f"{util_media:>10.3f} {viols:>12} {alertas_media:>8.1f}")

    print("="*65)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-llm", action="store_true")
    args = parser.parse_args()
    run_all_ablations(skip_llm=args.skip_llm)