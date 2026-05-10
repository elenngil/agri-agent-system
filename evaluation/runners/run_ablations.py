"""
run_ablations.py
----------------
Ejecuta los 4 estudios de ablación sobre los 15 escenarios.

Qué es una ablación:
  Desactivar o eliminar un componente del sistema para medir
  cuánto contribuye al rendimiento total. Si el rendimiento
  cae mucho sin un componente, ese componente es valioso.

Las 4 ablaciones:
  A0 - Sistema completo          (referencia)
  A1 - Sin CriticAgent           (¿qué aportan los guardarraíles?)
  A2 - Sin Graph RAG             (¿qué aporta el grafo de conocimiento?)
  A3 - Sin ningún RAG            (¿qué aporta el RAG en general?)
  A4 - Baseline LLM único        (¿qué aporta la arquitectura multiagente?)

Uso:
    python evaluation/runners/run_ablations.py
    python evaluation/runners/run_ablations.py --skip-llm
"""

import csv
import time
import sys
import traceback
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.shared_state import SharedState, RiskLevel
from agents.inference_agent import InferenceAgent
from agents.prediction_agent import PredictionAgent
from agents.risk_agent import RiskAgent
from agents.deliberative_agent import DeliberativeAgent
from agents.critic_agent import CriticAgent
from agents.daily_plan_agent import DailyPlanAgent

from evaluation.scenarios.test_scenarios import SCENARIOS
from evaluation.runners.run_pipeline import build_state_from_scenario, check_ground_truth

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

SEED = 42  # Usamos una sola seed para ablaciones (comparamos configuraciones, no varianza)


def run_ablation(scenario: dict, config: str, skip_llm: bool = False) -> dict:
    """
    Ejecuta un escenario con una configuración de ablación específica.

    config puede ser: "completo", "sin_critic", "sin_graph_rag",
                      "sin_rag", "baseline_llm"
    """
    fila = {
        "timestamp":   datetime.now().isoformat(),
        "scenario_id": scenario["id"],
        "scenario":    scenario["name"],
        "config":      config,
    }

    try:
        state = build_state_from_scenario(scenario)
        state = InferenceAgent().run(state)
        state = PredictionAgent().run(state)
        state = RiskAgent().run(state)

        critical = [a for a in state.alerts
                    if a.level in (RiskLevel.HIGH, RiskLevel.CRITICAL)]
        ruta = "urgente" if critical else "estandar"
        top_n = 1 if ruta == "urgente" else 3

        state = DeliberativeAgent().run(state, top_n=top_n)

        # Aplicar ablación
        critic_rechazos = 0
        violaciones = 0

        if config == "sin_critic":
            # No ejecutar el CriticAgent: medir cuántas violaciones ocurren
            critique = CriticAgent().run(state)  # Solo para medir, no para corregir
            if not critique["approved"]:
                violaciones += 1
            # No corregimos: dejamos pasar la recomendación tal cual

        elif config in ("completo", "sin_graph_rag", "sin_rag"):
            # CriticAgent activo (solo en ruta estándar)
            if ruta == "estandar":
                critique = CriticAgent().run(state)
                if not critique["approved"]:
                    critic_rechazos += 1
                    excluded = critique.get("problematic_actions", [])
                    state = DeliberativeAgent().run(
                        state, top_n=3, excluded_actions=excluded or None
                    )

        # ExplanationAgent con distintas fuentes de conocimiento
        if not skip_llm and config != "baseline_llm":
            try:
                import os
                from dotenv import load_dotenv
                from smolagents import InferenceClientModel
                load_dotenv()
                model = InferenceClientModel(
                    model_id="Qwen/Qwen2.5-72B-Instruct",
                    token=os.environ["HF_TOKEN"],
                )

                if config == "sin_graph_rag":
                    # Solo RAG semántico, sin grafo
                    from agents.explanation_agent import ExplanationAgent
                    agent = ExplanationAgent(llm_client=model)
                    agent.graph_retriever = None  # Desactivar grafo
                    state = agent.run(state)

                elif config == "sin_rag":
                    # Sin ningún RAG: prompt mínimo solo con datos del estado
                    from agents.explanation_agent import ExplanationAgent
                    agent = ExplanationAgent(llm_client=model)
                    agent.graph_retriever  = None
                    agent.chroma_retriever = None
                    state = agent.run(state)

                else:  # config == "completo"
                    from agents.explanation_agent import ExplanationAgent
                    state = ExplanationAgent(llm_client=model).run(state)

            except Exception as e:
                fila["explanation_error"] = str(e)

        elif config == "baseline_llm" and not skip_llm:
            # Baseline: un único LLM recibe todos los datos sin arquitectura multiagente
            try:
                import os
                from dotenv import load_dotenv
                from smolagents import InferenceClientModel, ChatMessage
                load_dotenv()
                model = InferenceClientModel(
                    model_id="Qwen/Qwen2.5-72B-Instruct",
                    token=os.environ["HF_TOKEN"],
                )
                w = state.weather_data
                c = state.crop_data
                prompt = f"""Eres un experto vitícola. Dados estos datos meteorológicos:
- Temperatura máxima: {w.temperature_max}°C
- Temperatura mínima: {w.temperature_min}°C
- Precipitación: {w.precipitation}mm
- Humedad: {w.humidity}%
- Variedad: {c.variety}
- Región: {state.ccaa}

Genera una recomendación de manejo del viñedo para hoy.
Incluye: riesgos detectados, acciones recomendadas y justificación."""
                response = model([ChatMessage(role="user", content=prompt)])
                fila["baseline_output"] = response.content[:500] if response else ""
            except Exception as e:
                fila["baseline_error"] = str(e)

        state = DailyPlanAgent().run(state)
        gt = check_ground_truth(state, scenario)

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
            "exito": False,
            "gt_pass": False,
            "errores": traceback.format_exc()[:300],
        })

    return fila


def run_all_ablations(skip_llm: bool = False) -> None:
    configs = ["completo", "sin_critic", "sin_graph_rag", "sin_rag"]
    filas = []

    total = len(SCENARIOS) * len(configs)
    completadas = 0

    for config in configs:
        print(f"\n{'='*50}")
        print(f"ABLACIÓN: {config}")
        print(f"{'='*50}")

        for scenario in SCENARIOS:
            completadas += 1
            print(f"  [{completadas}/{total}] {scenario['id']}", end=" ")

            fila = run_ablation(scenario, config, skip_llm=skip_llm)
            filas.append(fila)

            status = "✓" if fila.get("gt_pass") else "✗"
            util   = fila.get("utilidad", "—")
            viols  = fila.get("violaciones", 0)
            print(f"→ {status} utilidad={util} violaciones={viols}")

    output_path = RESULTS_DIR / "ablation_results.csv"
    if filas:
        campos = list(filas[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(filas)

    print(f"\n✅ Resultados guardados en {output_path}")
    _print_ablation_summary(filas, configs)


def _print_ablation_summary(filas: list[dict], configs: list[str]) -> None:
    print("\n" + "="*60)
    print("RESUMEN ABLACIONES")
    print(f"{'Config':<20} {'GT Pass':>8} {'Utilidad':>10} {'Violaciones':>12}")
    print("-"*60)

    for config in configs:
        subset = [f for f in filas if f.get("config") == config]
        gt_pass = sum(1 for f in subset if f.get("gt_pass"))
        utils   = [f["utilidad"] for f in subset if "utilidad" in f]
        viols   = sum(f.get("violaciones", 0) for f in subset)

        import statistics
        util_media = statistics.mean(utils) if utils else 0

        print(f"{config:<20} {gt_pass:>4}/{len(subset):<4} "
              f"{util_media:>10.3f} {viols:>12}")

    print("="*60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-llm", action="store_true")
    args = parser.parse_args()
    run_all_ablations(skip_llm=args.skip_llm)