import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

RESULTS_DIR = Path(__file__).parent.parent / "results"
OUTPUT_DIR  = Path(__file__).parent.parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

VERDE_OSCURO = "#3B6011"
VERDE_MEDIO  = "#5A7830"
TIERRA       = "#8B5E3C"
OCRE         = "#C8A870"
CREMA        = "#F5F0E8"
MARRON_ROJO  = "#8B3010"
GRIS         = "#9B8E7E"

plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "font.size":         10,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "figure.facecolor":  "white",
    "axes.facecolor":    "#F5F0E8",
})


def plot_latency_by_agent():
    csv_path = RESULTS_DIR / "pipeline_results.csv"
    if not csv_path.exists():
        print(f"  No encontrado: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    agentes = ["inference", "prediction", "risk", "deliberative", "critic", "explanation", "daily_plan"]
    cols    = [f"t_{a}" for a in agentes if f"t_{a}" in df.columns]

    if not cols:
        print("  No hay columnas de latencia en pipeline_results.csv")
        return

    medias = df[cols].mean()
    stds   = df[cols].std()
    labels = [c.replace("t_", "").capitalize() for c in cols]
    colores = [MARRON_ROJO if "expl" in c else VERDE_OSCURO for c in cols]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(labels, medias, yerr=stds, color=colores,
                  error_kw={"elinewidth": 1.5, "capsize": 4, "color": GRIS},
                  width=0.6, zorder=3)

    ax.set_ylabel("Latencia media (segundos)", fontsize=11)
    ax.set_title("Latencia media por agente (n=" + str(len(df)) + " ejecuciones)",
                 fontsize=12, fontweight="bold", pad=12)
    ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)

    for bar, media in zip(bars, medias):
        if media > 0.01:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f"{media:.1f}s", ha="center", va="bottom", fontsize=9, color="#2C2416")

    patch_normal = mpatches.Patch(color=VERDE_OSCURO, label="Agentes deterministas")
    patch_llm    = mpatches.Patch(color=MARRON_ROJO,  label="ExplanationAgent (LLM)")
    ax.legend(handles=[patch_normal, patch_llm], loc="upper left", framealpha=0.9)

    plt.tight_layout()
    out = OUTPUT_DIR / "latency_by_agent.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  {out}")


def plot_robustness_boxplot():
    csv_path = RESULTS_DIR / "robustness_results.csv"
    if not csv_path.exists():
        print(f"  No encontrado: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    temps = sorted(df["temperature"].unique())

    fig, ax = plt.subplots(figsize=(9, 5))
    data_por_temp = []
    labels = []

    for temp in temps:
        subset = df[df["temperature"] == temp]
        valores = []
        for _, row in subset.iterrows():
            np.random.seed(42)
            muestra = np.random.normal(
                loc=row["utilidad_media"],
                scale=max(row["utilidad_std"], 0.001),
                size=100
            )
            muestra = np.clip(muestra, 0, 1)
            valores.extend(muestra.tolist())
        data_por_temp.append(valores)
        labels.append(f"T = {temp:.2f}")

    bp = ax.boxplot(data_por_temp, labels=labels, patch_artist=True,
                    medianprops={"color": TIERRA, "linewidth": 2},
                    whiskerprops={"color": GRIS},
                    capprops={"color": GRIS},
                    flierprops={"marker": "o", "markersize": 3,
                                "markerfacecolor": GRIS, "alpha": 0.5})

    colores_box = [VERDE_OSCURO, VERDE_MEDIO, OCRE, MARRON_ROJO]
    for patch, color in zip(bp["boxes"], colores_box[:len(bp["boxes"])]):
        patch.set_facecolor(color)
        patch.set_alpha(0.65)

    ax.set_ylabel("Utilidad del escenario seleccionado", fontsize=11)
    ax.set_xlabel("Nivel de perturbacion (temperature)", fontsize=11)
    ax.set_title("Robustez del DeliberativeAgent ante perturbaciones gaussianas",
                 fontsize=12, fontweight="bold", pad=12)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_ylim(0, 1)

    plt.tight_layout()
    out = OUTPUT_DIR / "robustness_boxplot.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  {out}")


def plot_ablation_table():
    csv_path = RESULTS_DIR / "ablation_results.csv"
    if not csv_path.exists():
        print(f"  No encontrado: {csv_path}")
        return

    df = pd.read_csv(csv_path)

    CONFIGS_ORDEN = [
        ("completo",       "Completo (referencia)"),
        ("sin_fase1",      "Sin datos AEMET"),
        ("sin_inference",  "Sin InferenceAgent"),
        ("sin_prediction", "Sin PredictionAgent"),
        ("sin_routing",    "Sin routing condicional"),
        ("sin_critic",     "Sin CriticAgent"),
        ("sin_rag",        "Sin RAG"),
    ]

    resumen = []
    for config, label in CONFIGS_ORDEN:
        sub = df[df["config"] == config]
        if sub.empty:
            continue
        gt_pct   = sub["gt_pass"].mean() * 100   if "gt_pass"   in sub else 0
        util     = sub["utilidad"].mean()          if "utilidad"  in sub else 0
        viols    = sub["violaciones"].sum()        if "violaciones" in sub else 0
        alertas  = sub["n_alertas"].mean()         if "n_alertas" in sub else 0
        resumen.append({
            "Configuracion":    label,
            "GT Pass (%)":      round(gt_pct, 1),
            "Utilidad media":   round(util, 3),
            "Violaciones":      int(viols),
            "Alertas (media)":  round(alertas, 1),
        })

    if not resumen:
        print("  Sin datos de ablacion")
        return

    df_res = pd.DataFrame(resumen)
    n_filas = len(df_res)

    fig, ax = plt.subplots(figsize=(12, 1.0 + n_filas * 0.55))
    ax.axis("off")

    tabla = ax.table(
        cellText=df_res.values,
        colLabels=df_res.columns,
        loc="center",
        cellLoc="center",
    )
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(9.5)
    tabla.scale(1.0, 1.9)

    for j in range(len(df_res.columns)):
        tabla[0, j].set_facecolor(VERDE_OSCURO)
        tabla[0, j].set_text_props(color="white", fontweight="bold")

    for j in range(len(df_res.columns)):
        tabla[1, j].set_facecolor("#E8DFC0")

    for i, row in enumerate(resumen):
        if row["Violaciones"] > 0:
            for j in range(len(df_res.columns)):
                tabla[i + 1, j].set_facecolor("#F5D5C0")

    for i, row in enumerate(resumen):
        if row["GT Pass (%)"] < 80 and row["Violaciones"] == 0 and i > 0:
            for j in range(len(df_res.columns)):
                tabla[i + 1, j].set_facecolor("#FFF3C8")

    ax.set_title("Tabla de ablaciones por capas — Contribucion de cada componente",
                 fontsize=12, fontweight="bold", pad=16, y=1.0)

    plt.tight_layout()
    out = OUTPUT_DIR / "ablation_table.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  {out}")


def plot_routing_distribution():
    csv_path = RESULTS_DIR / "pipeline_results.csv"
    if not csv_path.exists():
        print(f"  No encontrado: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    if "ruta" not in df.columns:
        print("  Columna 'ruta' no encontrada")
        return

    counts = df["ruta"].value_counts()
    total  = len(df)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    colores_pie = [MARRON_ROJO if r == "urgente" else VERDE_OSCURO for r in counts.index]
    ax1.pie(counts.values,
            labels=[f"{r.capitalize()}\n({v/total:.0%})"
                    for r, v in zip(counts.index, counts.values)],
            colors=colores_pie, autopct="", startangle=90,
            wedgeprops={"edgecolor": "white", "linewidth": 2})
    ax1.set_title("Distribucion de rutas\n(total ejecuciones)", fontsize=11)

    if "scenario_id" in df.columns:
        grupos = {
            "Normal (S01-S03)":   ["S01","S02","S03"],
            "Mildiu (S04-S06)":   ["S04","S05","S06"],
            "Hidrico (S07-S09)":  ["S07","S08","S09"],
            "Helada (S10-S11)":   ["S10","S11"],
            "Multiple (S12-S15)": ["S12","S13","S14","S15"],
        }
        urgente_pct = []
        nombres = []
        for nombre, ids in grupos.items():
            sub = df[df["scenario_id"].isin(ids)]
            if not sub.empty:
                pct = (sub["ruta"] == "urgente").mean() * 100
                urgente_pct.append(pct)
                nombres.append(nombre)

        colores_bar = [VERDE_OSCURO if p < 50 else MARRON_ROJO for p in urgente_pct]
        bars = ax2.barh(nombres, urgente_pct, color=colores_bar, height=0.5)
        ax2.set_xlabel("% de ejecuciones con ruta urgente", fontsize=10)
        ax2.set_title("Activacion de ruta urgente\npor grupo de escenario", fontsize=11)
        ax2.set_xlim(0, 100)
        ax2.axvline(50, color=GRIS, linestyle="--", alpha=0.5)
        ax2.grid(axis="x", linestyle="--", alpha=0.3)

        for bar, pct in zip(bars, urgente_pct):
            ax2.text(pct + 1, bar.get_y() + bar.get_height()/2,
                     f"{pct:.0f}%", va="center", fontsize=9)

    plt.suptitle("Analisis del routing condicional del orquestador",
                 fontsize=12, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = OUTPUT_DIR / "routing_distribution.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  {out}")


if __name__ == "__main__":
    print("\n" + "="*50)
    print("Generando graficos del TFG (paleta tierra)...")
    print("="*50)

    print("\n1. Latencia por agente")
    plot_latency_by_agent()

    print("\n2. Boxplot de robustez")
    plot_robustness_boxplot()

    print("\n3. Tabla de ablaciones")
    plot_ablation_table()

    print("\n4. Distribucion de routing")
    plot_routing_distribution()

    print(f"\nGraficos guardados en {OUTPUT_DIR}")