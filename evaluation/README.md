# Evaluación del Sistema — AgroVid

## Orden de ejecución

Ejecuta los scripts en este orden exacto desde la raíz del proyecto:

```bash
# 1. Evaluación principal del pipeline (rápida, sin LLM)
python evaluation/runners/run_pipeline.py --skip-llm

# 2. Misma evaluación CON el ExplanationAgent (lenta, ~30min)
python evaluation/runners/run_pipeline.py

# 3. Ablaciones (sin LLM para rapidez)
python evaluation/runners/run_ablations.py --skip-llm

# 4. Análisis de robustez (sin LLM, solo DeliberativeAgent)
python evaluation/runners/run_robustness.py

# 5. Métricas del RAG (sin LLM)
python evaluation/metrics/rag_metrics.py

# 6. Generar gráficos
python evaluation/analysis/generate_plots.py
```

## Estructura de resultados

Después de ejecutar todo, `evaluation/results/` contendrá:

| Fichero | Qué contiene |
|---------|-------------|
| `pipeline_results.csv` | Latencias, success rate, ground truth por escenario y seed |
| `ablation_results.csv` | Comparativa de las 4 configuraciones de ablación |
| `robustness_results.csv` | Estadísticos de utilidad por nivel de temperature |

Y `evaluation/outputs/` contendrá los 5 PNG para el TFG.

## Qué mide cada script

### run_pipeline.py
Ejecuta los 15 escenarios con 5 seeds. Para cada ejecución mide:
- Latencia de cada agente por separado
- Qué ruta activó el orquestador (urgente/estándar)
- Cuántas veces rechazó el CriticAgent
- Utilidad del escenario seleccionado
- Si se cumplió el ground truth esperado

### run_ablations.py
Ejecuta 4 configuraciones para demostrar el valor de cada componente:
- **completo**: sistema tal como está
- **sin_critic**: sin guardarraíles (mide violaciones no corregidas)
- **sin_graph_rag**: solo ChromaDB, sin el grafo de conocimiento
- **sin_rag**: sin ninguna fuente de conocimiento externa

### run_robustness.py
Ejecuta el DeliberativeAgent 100 veces por escenario con temperature
en {0.0, 0.03, 0.05, 0.10}. Mide si la recomendación cambia o se mantiene.

### rag_metrics.py
Comprueba que el grafo de conocimiento tiene cobertura para los 5 tipos
de riesgo del sistema y que ChromaDB está operativo.

## Fechas de los escenarios

Todos los escenarios usan datos de 2024 (históricamente disponibles en AEMET).
Con `--skip-llm` y `weather_override`, los tests no requieren conexión a AEMET.