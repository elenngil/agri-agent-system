import json
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="AgroVid · Panel de Manejo",
    page_icon="🍇",
    layout="wide",
)

DATA_PATH = Path("output/daily_plan.json")


@st.cache_data(ttl=30)
def load_data():
    if not DATA_PATH.exists():
        return None
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


data = load_data()

if not data:
    st.error("No hay datos disponibles. Ejecuta el pipeline primero.")
    st.stop()

meta = data["meta"]
plan = data.get("daily_plan", {})
exp = data.get("explanation_agent", {})
climate = plan.get("climate", {})
irr = plan.get("irrigation", {})
crop = plan.get("crop_status", {})
prev = plan.get("prevention", [])

st.title("🍇 Panel de Manejo del Viñedo")
st.caption(
    f"📍 {meta['region']} · {meta['station']} · "
    f"{meta['start_date']} → {meta['end_date']} · "
    f"Variedad: {meta['variety']}"
)
st.divider()

st.subheader("📱 Resumen SMS")
st.info(data.get("sms", "—"))
st.divider()

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="💧 Riego recomendado",
    value=f"{irr.get('adjusted_liters', '—')} L/m²",
    delta=f"base {irr.get('base_liters', '—')} L/m²",
)
col2.metric(
    label="🌡️ Temp. máxima",
    value=f"{climate.get('temp_max', '—')} °C",
    delta=f"mín {climate.get('temp_min', '—')} °C",
)
col3.metric(
    label="💦 Precipitación",
    value=f"{climate.get('precipitation', '—')} mm",
)
col4.metric(
    label="🌱 Fase del cultivo",
    value=str(crop.get("phase", "—")).capitalize(),
)

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("🌤️ Condiciones climáticas")

    condition = climate.get("condition", "—")
    color_map = {
        "óptimo": "✅",
        "estrés térmico": "🌡️",
        "riesgo de helada": "🥶",
        "frío": "❄️",
        "húmedo": "🌫️",
    }
    icon = color_map.get(condition, "🌤️")
    st.markdown(f"### {icon} {str(condition).capitalize()}")
    st.write(climate.get("interpretation", ""))

    st.markdown(f"- **Humedad:** {climate.get('humidity', '—')} %")
    st.markdown(f"- **Precipitación:** {climate.get('precipitation', '—')} mm")

with right:
    st.subheader("💧 Plan de riego")
    st.markdown(f"**{irr.get('adjusted_liters', '—')} L/m²** recomendados")
    st.write(f"_{irr.get('adjustment_reason', '')}_")
    st.markdown(f"- **Multiplicador de suelo:** ×{irr.get('soil_multiplier', 1.0)}")

    if irr.get("assumed_values"):
        st.warning(
            "Valores asumidos por falta de datos: "
            + ", ".join(irr["assumed_values"])
        )

st.divider()

st.subheader("🌱 Estado del cultivo")
assumed_note = " _(fase estimada por mes)_" if crop.get("assumed") else ""
st.markdown(f"**Fase:** {str(crop.get('phase', '—')).capitalize()}{assumed_note}")
st.write(crop.get("recommendation", ""))

st.divider()

st.subheader("⚠️ Prevención y alertas")

priority_color = {"alta": "🔴", "media": "🟡", "baja": "🟢"}

for item in prev:
    icon = priority_color.get(item.get("priority"), "⚪")
    label = item.get("label", "—")
    action = item.get("action", "")
    prio = item.get("priority", "—")

    with st.expander(f"{icon} {label} — prioridad {prio}"):
        st.write(action)

st.divider()

st.subheader("🧠 Explicación del plan")
st.write(plan.get("explanation", "Sin explicación disponible."))

if exp.get("summary"):
    with st.expander("📋 Resumen del agente de explicación"):
        st.write(exp["summary"])

        conf = exp.get("confidence", {})
        if conf:
            st.markdown(
                f"**Confianza:** {conf.get('label', '—')} "
                f"({conf.get('score', '—')})"
            )
            if conf.get("reasons"):
                st.markdown("Motivos: " + ", ".join(conf["reasons"]))

if exp.get("alternatives"):
    st.divider()
    st.subheader("🔀 Escenarios alternativos")

    for i, alt in enumerate(exp["alternatives"], 1):
        utility = alt.get("utility")
        utility_text = f"{utility:.2f}" if isinstance(utility, (int, float)) else "—"

        with st.expander(f"Alternativa {i} — utilidad {utility_text}"):
            st.write(alt.get("summary", ""))
            for action in alt.get("actions", []):
                st.markdown(
                    f"- **{action.get('type_label', action.get('type'))}**: "
                    f"{action.get('intensity_label', action.get('intensity'))} "
                    f"(coste {action.get('cost', 0):.2f})"
                )

st.divider()
st.caption("AgroVid · Sistema de apoyo a la decisión vitícola · TFG")