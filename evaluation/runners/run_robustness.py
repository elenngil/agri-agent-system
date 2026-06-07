import csv
import random
import statistics
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.shared_state import RiskLevel
from agents.inference_agent import InferenceAgent
from agents.prediction_agent import PredictionAgent
from agents.risk_agent import RiskAgent
from agents.deliberative_agent import DeliberativeAgent

from evaluation.scenarios.test_scenarios import SCENARIOS
from evaluation.runners.run_pipeline import build_state_from_scenario

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

ROBUSTNESS_SCENARIOS = ["S01", "S04", "S07", "S10", "S12"]

TEMPERATURES = [0.0, 0.03, 0.05, 0.10]
N_ITERATIONS = 100


def run_robustness_analysis() -> None:
    filas = []

    scenarios_subset = [s for s in SCENARIOS if s["id"] in ROBUSTNESS_SCENARIOS]

    for scenario in scenarios_subset:
        print(f"\n{'='*50}")
        print(f"Escenario: {scenario['id']} — {scenario['name']}")

        # Construir el estado base una sola vez
        state_base = build_state_from_scenario(scenario)
        state_base = InferenceAgent().run(state_base)
        state_base = PredictionAgent().run(state_base)
        state_base = RiskAgent().run(state_base)

        for temp in TEMPERATURES:
            utilidades = []
            acciones_top = []

            for i in range(N_ITERATIONS):
                random.seed(i * 1000 + int(temp * 1000))

                agent = DeliberativeAgent(temperature=temp)

                import copy
                state_copy = copy.deepcopy(state_base)

                critical = [a for a in state_copy.alerts
                            if a.level in (RiskLevel.HIGH, RiskLevel.CRITICAL)]
                top_n = 1 if critical else 3

                state_copy = agent.run(state_copy, top_n=top_n)

                if state_copy.scenarios:
                    utilidades.append(state_copy.scenarios[0].utility)
                    best_action = max(
                        state_copy.scenarios[0].actions,
                        key=lambda a: a.cost,
                        default=None
                    )
                    if best_action:
                        acciones_top.append(f"{best_action.type}:{best_action.intensity}")

            if utilidades:
                media  = statistics.mean(utilidades)
                std    = statistics.stdev(utilidades) if len(utilidades) > 1 else 0
                minimo = min(utilidades)
                maximo = max(utilidades)

                if acciones_top:
                    from collections import Counter
                    moda = Counter(acciones_top).most_common(1)[0][0]
                    tasa_cambio = sum(1 for a in acciones_top if a != moda) / len(acciones_top)
                else:
                    tasa_cambio = 0.0
                    moda = "—"

                fila = {
                    "scenario_id":  scenario["id"],
                    "scenario":     scenario["name"][:40],
                    "temperature":  temp,
                    "n_iter":       len(utilidades),
                    "utilidad_media": round(media, 4),
                    "utilidad_std":   round(std, 4),
                    "utilidad_min":   round(minimo, 4),
                    "utilidad_max":   round(maximo, 4),
                    "tasa_cambio_recomendacion": round(tasa_cambio, 3),
                    "accion_mas_frecuente": moda,
                }
                filas.append(fila)

                print(f"  temp={temp:.2f} → μ={media:.4f} σ={std:.4f} "
                      f"cambios={tasa_cambio:.1%}")

    output_path = RESULTS_DIR / "robustness_results.csv"
    if filas:
        campos = list(filas[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            writer.writerows(filas)

    print(f"\n✅ Resultados guardados en {output_path}")
    _print_robustness_summary(filas)


def _print_robustness_summary(filas: list[dict]) -> None:
    print("\n" + "="*70)
    print("RESUMEN ROBUSTEZ — Desviación típica de utilidad por temperatura")
    print(f"{'Escenario':<10} {'Temp':>6} {'Media':>8} {'Std':>8} {'Cambios':>10}")
    print("-"*70)
    for fila in filas:
        print(f"{fila['scenario_id']:<10} {fila['temperature']:>6.2f} "
              f"{fila['utilidad_media']:>8.4f} {fila['utilidad_std']:>8.4f} "
              f"{fila['tasa_cambio_recomendacion']:>9.1%}")
    print("="*70)


if __name__ == "__main__":
    run_robustness_analysis()