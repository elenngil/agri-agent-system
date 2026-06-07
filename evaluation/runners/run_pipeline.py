import csv
import time
import argparse
import traceback
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.shared_state import SharedState, RiskLevel
from agents.inference_agent import InferenceAgent
from agents.prediction_agent import PredictionAgent
from agents.risk_agent import RiskAgent
from agents.deliberative_agent import DeliberativeAgent
from agents.critic_agent import CriticAgent
from agents.daily_plan_agent import DailyPlanAgent

from evaluation.scenarios.test_scenarios import SCENARIOS

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

SEEDS = [42, 123, 456, 789, 1337]


def build_state_from_scenario(scenario: dict) -> SharedState:
    state = SharedState(
        station=scenario["station"],
        start_date=scenario["start_date"],
        end_date=scenario["end_date"],
        ccaa=scenario["ccaa"],
    )
    state.crop_data       = scenario["crop"]
    state.soil_multiplier = 1.0

    if scenario.get("weather_override") is not None:
        state.weather_data = scenario["weather_override"]
    else:
        from agents.observation_agent import ObservationAgent
        state = ObservationAgent().run(state)

    return state


def run_agents(state: SharedState, skip_llm: bool = False) -> tuple[dict, SharedState]:
    tiempos = {}
    errores = []

    # 1. InferenceAgent
    t0 = time.perf_counter()
    try:
        state = InferenceAgent().run(state)
    except Exception as e:
        errores.append(f"InferenceAgent: {e}")
        print(f"\n    WARN InferenceAgent: {e}")
    tiempos["inference"] = round(time.perf_counter() - t0, 3)

    t0 = time.perf_counter()
    try:
        state = PredictionAgent().run(state)
    except Exception as e:
        errores.append(f"PredictionAgent: {e}")
        print(f"\n    WARN PredictionAgent: {e}")
    tiempos["prediction"] = round(time.perf_counter() - t0, 3)

    t0 = time.perf_counter()
    try:
        state = RiskAgent().run(state)
    except Exception as e:
        errores.append(f"RiskAgent: {e}")
        print(f"\n    WARN RiskAgent: {e}")
    tiempos["risk"] = round(time.perf_counter() - t0, 3)

    critical = [a for a in state.alerts
                if a.level in (RiskLevel.HIGH, RiskLevel.CRITICAL)]
    ruta  = "urgente" if critical else "estandar"
    top_n = 1 if ruta == "urgente" else 3

    t0 = time.perf_counter()
    try:
        state = DeliberativeAgent().run(state, top_n=top_n)
    except Exception as e:
        errores.append(f"DeliberativeAgent: {e}")
        print(f"\n    WARN DeliberativeAgent: {e}")
    tiempos["deliberative"] = round(time.perf_counter() - t0, 3)

    critic_rechazos = 0
    tiempos["critic"] = 0.0
    if ruta == "estandar" and state.scenarios:
        t0 = time.perf_counter()
        try:
            critique = CriticAgent().run(state)
            if not critique["approved"]:
                critic_rechazos += 1
                excluded = critique.get("problematic_actions", [])
                state = DeliberativeAgent().run(
                    state, top_n=3, excluded_actions=excluded or None
                )
                critique2 = CriticAgent().run(state)
                if not critique2["approved"]:
                    critic_rechazos += 1
        except Exception as e:
            errores.append(f"CriticAgent: {e}")
            print(f"\n    WARN CriticAgent: {e}")
        tiempos["critic"] = round(time.perf_counter() - t0, 3)

    tiempos["explanation"] = 0.0
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
            t0 = time.perf_counter()
            state = ExplanationAgent(llm_client=model).run(state)
            tiempos["explanation"] = round(time.perf_counter() - t0, 3)
        except Exception as e:
            errores.append(f"ExplanationAgent: {e}")
            print(f"\n    WARN ExplanationAgent: {e}")

    t0 = time.perf_counter()
    try:
        state = DailyPlanAgent().run(state)
    except Exception as e:
        errores.append(f"DailyPlanAgent: {e}")
        print(f"\n    WARN DailyPlanAgent: {e}")
    tiempos["daily_plan"] = round(time.perf_counter() - t0, 3)

    tiempos["total"] = round(sum(v for k, v in tiempos.items() if k != "total"), 3)

    metricas = {
        "ruta":            ruta,
        "n_alertas":       len(state.alerts),
        "alertas":         "|".join(a.risk_type for a in state.alerts),
        "critic_rechazos": critic_rechazos,
        "utilidad":        round(state.scenarios[0].utility, 4) if state.scenarios else 0.0,
        "exito":           len(errores) == 0 and state.daily_plan is not None,
        "errores":         "; ".join(errores),
        **{f"t_{k}": v for k, v in tiempos.items()},
    }

    return metricas, state


def check_ground_truth(state: SharedState, scenario: dict) -> dict:
    
    detected_risks = {a.risk_type for a in state.alerts}
    best_actions   = {(a.type, a.intensity) for a in state.scenarios[0].actions} \
                     if state.scenarios else set()

    alerts_ok = all(r in detected_risks for r in scenario["expected_alerts"])

    actions_ok = all(
        any(atype == exp_type and aintensity != "none"
            for atype, aintensity in best_actions)
        for exp_type, _ in scenario["expected_actions"]
    ) if scenario["expected_actions"] else True

    critic_ok = True
    if state.scenarios:
        critique  = CriticAgent().run(state)
        critic_ok = critique["approved"] == scenario["should_critic_approve"]

    return {
        "gt_alerts_ok":  alerts_ok,
        "gt_actions_ok": actions_ok,
        "gt_critic_ok":  critic_ok,
        "gt_pass":       alerts_ok and actions_ok and critic_ok,
    }


def run_all(seeds: list[int], skip_llm: bool = False) -> None:
    output_path = RESULTS_DIR / "pipeline_results.csv"
    filas = []
    total = len(SCENARIOS) * len(seeds)
    completadas = 0

    for scenario in SCENARIOS:
        for seed in seeds:
            completadas += 1
            print(f"[{completadas}/{total}] {scenario['id']} seed={seed}", end=" ")

            fila = {
                "timestamp":   datetime.now().isoformat(),
                "scenario_id": scenario["id"],
                "scenario":    scenario["name"],
                "seed":        seed,
                "station":     scenario["station"],
                "ccaa":        scenario["ccaa"],
            }

            try:
                state = build_state_from_scenario(scenario)
                metricas, state = run_agents(state, skip_llm=skip_llm)
                gt = check_ground_truth(state, scenario)

                # Justo después de gt = check_ground_truth(state, scenario)
                if not gt["gt_pass"] and scenario["id"] in ("S06", "S15"):
                    print(f"   DEBUG gt_alerts_ok={gt['gt_alerts_ok']} "
                        f"gt_actions_ok={gt['gt_actions_ok']} "
                        f"gt_critic_ok={gt['gt_critic_ok']}")
                    print(f"   alertas detectadas: {[a.risk_type for a in state.alerts]}")
                    if state.scenarios:
                        print(f"   acciones top: {[(a.type, a.intensity) for a in state.scenarios[0].actions]}")

                fila.update(metricas)
                fila.update(gt)

                status = "PASS" if gt["gt_pass"] else "FAIL"
                print(f"-> utilidad={metricas['utilidad']} "
                      f"alertas={metricas['n_alertas']} "
                      f"ruta={metricas['ruta']} {status}")
                if metricas["errores"]:
                    print(f"   errores: {metricas['errores']}")

            except Exception as e:
                fila.update({
                    "exito":   False,
                    "errores": traceback.format_exc()[:500],
                    "gt_pass": False,
                })
                print(f"-> ERROR: {e}")
                traceback.print_exc()

            filas.append(fila)

    if filas:
        campos = list(filas[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(filas)

    print(f"\nResultados guardados en {output_path}")
    _print_summary(filas)


def _print_summary(filas: list[dict]) -> None:
    total    = len(filas)
    exitosos = sum(1 for f in filas if f.get("exito"))
    gt_pass  = sum(1 for f in filas if f.get("gt_pass"))
    lat_total = [f["t_total"] for f in filas if "t_total" in f and f["t_total"] > 0]

    print("\n" + "="*50)
    print("RESUMEN DE EVALUACION")
    print("="*50)
    print(f"Ejecuciones totales:   {total}")
    print(f"Exito tecnico:         {exitosos}/{total} ({100*exitosos/total:.1f}%)")
    print(f"Ground truth pasado:   {gt_pass}/{total} ({100*gt_pass/total:.1f}%)")
    if lat_total:
        import statistics
        print(f"Latencia media total:  {statistics.mean(lat_total):.3f}s")
        print(f"Latencia P95:          {sorted(lat_total)[int(0.95*len(lat_total))]:.3f}s")
    print("="*50)

    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--skip-llm", action="store_true")
    args = parser.parse_args()
    run_all(seeds=SEEDS[:args.seeds], skip_llm=args.skip_llm)