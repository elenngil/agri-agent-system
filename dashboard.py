import json
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="AgroVid · Dashboard Técnico",
    page_icon="🍇",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --verde-vid:   #3B6B2A;
    --verde-claro: #5A8F45;
    --tierra:      #8B5E3C;
    --ocre:        #C8832A;
    --crema:       #F5F0E8;
    --blanco:      #FDFCF9;
    --gris-suave:  #E8E2D9;
    --texto:       #2C2416;
    --texto-suave: #6B5E4E;
    --rojo:        #C0392B;
    --amarillo:    #D4A017;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: var(--texto);
    background-color: var(--blanco);
}
h1, h2, h3 { font-family: 'Playfair Display', serif; }

.stApp { background-color: var(--blanco); }

[data-testid="metric-container"] {
    background-color: var(--crema);
    border: 1px solid var(--gris-suave);
    border-radius: 14px;
    padding: 1rem 1.2rem;
}
[data-testid="metric-container"] label {
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--texto-suave) !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif !important;
    font-size: 1.9rem !important;
    color: var(--verde-vid) !important;
}

.sms-banner {
    background: linear-gradient(135deg, #3B6B2A, #5A8F45);
    color: white;
    border-radius: 14px;
    padding: 1.2rem 1.8rem;
    font-size: 1rem;
    line-height: 1.7;
    margin-bottom: 1.5rem;
}

.card {
    background: var(--crema);
    border: 1px solid var(--gris-suave);
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    height: 100%;
}
.card-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--verde-vid);
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.fase-badge {
    display: inline-block;
    background: var(--verde-vid);
    color: white;
    border-radius: 20px;
    padding: 0.2rem 0.9rem;
    font-size: 0.82rem;
    font-weight: 500;
    margin-bottom: 0.6rem;
}

.prev-item {
    display: flex;
    align-items: flex-start;
    gap: 0.7rem;
    padding: 0.9rem 1rem;
    border-radius: 10px;
    margin-bottom: 0.5rem;
    border: 1px solid var(--gris-suave);
    background: var(--blanco);
    transition: border-color 0.2s;
}
.prev-item:hover { border-color: var(--verde-vid); }
.prev-alta   { border-left: 4px solid var(--rojo) !important; }
.prev-media  { border-left: 4px solid var(--amarillo) !important; }
.prev-baja   { border-left: 4px solid var(--verde-claro) !important; }

.stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.4rem 0;
    border-bottom: 1px solid var(--gris-suave);
    font-size: 0.9rem;
}
.stat-row:last-child { border-bottom: none; }
.stat-label { color: var(--texto-suave); }
.stat-value { font-weight: 500; }

.divider { border: none; border-top: 2px solid var(--gris-suave); margin: 1.5rem 0; }

.cond-icon { font-size: 2rem; margin-bottom: 0.3rem; }
</style>
""", unsafe_allow_html=True)

# ── Datos ─────────────────────────────────────────────────────────────────────
DATA_PATH = Path("output/daily_plan.json")

@st.cache_data(ttl=30)
def load_data():
    if not DATA_PATH.exists():
        return None
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)

data = load_data()

if not data:
    st.markdown("""
    <div style="text-align:center; padding:4rem 2rem;">
        <div style="font-size:3rem; margin-bottom:1rem;">🌿</div>
        <h2 style="font-family:'Playfair Display',serif; color:#3B6B2A;">
            Sin datos disponibles
        </h2>
        <p style="color:#6B5E4E;">Ejecuta el pipeline primero para ver el dashboard.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

meta    = data.get("meta", {})
plan    = data.get("daily_plan", {})
exp     = data.get("explanation_agent", {})
climate = plan.get("climate", {})
irr     = plan.get("irrigation", {})
crop    = plan.get("crop_status", {})
prev    = plan.get("prevention", [])

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex; align-items:baseline; gap:12px; margin-bottom:0.3rem;">
    <h1 style="font-family:'Playfair Display',serif; color:#3B6B2A; margin:0; font-size:2rem;">
        🍇 AgroVid · Dashboard
    </h1>
</div>
<p style="color:#6B5E4E; font-size:0.88rem; margin-bottom:1.5rem;">
    📍 {meta.get('region','—')} &nbsp;·&nbsp;
    🌡 Estación {meta.get('station','—')} &nbsp;·&nbsp;
    📅 {meta.get('start_date','—')} → {meta.get('end_date','—')} &nbsp;·&nbsp;
    🌿 {meta.get('variety','—')}
</p>
""", unsafe_allow_html=True)

# ── SMS banner ────────────────────────────────────────────────────────────────
sms = data.get("sms", "")
if sms:
    st.markdown(f"""
    <div class="sms-banner">
        <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em;
                    opacity:0.7; margin-bottom:0.4rem;">📱 Notificación SMS del día</div>
        {sms.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

# ── Métricas principales ──────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("💧 Riego recomendado",
          f"{irr.get('adjusted_liters','—')} L/m²",
          delta=f"base {irr.get('base_liters','—')} L/m²")
c2.metric("🌡️ Temperatura máx.",
          f"{climate.get('temp_max','—')} °C",
          delta=f"mín {climate.get('temp_min','—')} °C")
c3.metric("💦 Precipitación",
          f"{climate.get('precipitation','—')} mm")
c4.metric("🌱 Fase del cultivo",
          str(crop.get("phase", "—")).capitalize())

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── Fila 1: Clima + Riego ─────────────────────────────────────────────────────
col_clima, col_riego = st.columns(2)

condition_map = {
    "óptimo":         ("✅", "#3B6B2A"),
    "estrés térmico": ("🌡️", "#C0392B"),
    "riesgo de helada":("🥶", "#185FA5"),
    "frío":           ("❄️", "#185FA5"),
    "húmedo":         ("🌫️", "#5A7A9F"),
}

with col_clima:
    cond  = climate.get("condition", "—")
    icon, color = condition_map.get(str(cond).lower(), ("🌤️", "#3B6B2A"))
    st.markdown(f"""
    <div class="card">
        <div class="card-title">🌤️ Condiciones climáticas</div>
        <div style="display:flex; align-items:center; gap:0.7rem; margin-bottom:0.8rem;">
            <span style="font-size:2rem;">{icon}</span>
            <span style="font-family:'Playfair Display',serif; font-size:1.2rem;
                         color:{color}; font-weight:600;">
                {str(cond).capitalize()}
            </span>
        </div>
        <p style="color:#6B5E4E; font-size:0.9rem; margin-bottom:0.8rem; line-height:1.6;">
            {climate.get('interpretation','')}
        </p>
        <div class="stat-row">
            <span class="stat-label">💧 Humedad</span>
            <span class="stat-value">{climate.get('humidity','—')} %</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">🌧️ Precipitación</span>
            <span class="stat-value">{climate.get('precipitation','—')} mm</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">🌡️ Temp. mínima</span>
            <span class="stat-value">{climate.get('temp_min','—')} °C</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">🌡️ Temp. máxima</span>
            <span class="stat-value">{climate.get('temp_max','—')} °C</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_riego:
    assumed = irr.get("assumed_values", [])
    assumed_html = ""
    if assumed:
        assumed_html = f"""
        <div style="background:#FFF3CD; border-radius:8px; padding:0.5rem 0.8rem;
                    font-size:0.8rem; color:#856404; margin-top:0.8rem;">
            ⚠️ Valores estimados: {', '.join(assumed)}
        </div>"""
    st.markdown(f"""
    <div class="card">
        <div class="card-title">💧 Plan de riego</div>
        <div style="font-family:'Playfair Display',serif; font-size:2rem;
                    color:#3B6B2A; font-weight:700; margin-bottom:0.3rem;">
            {irr.get('adjusted_liters','—')} L/m²
        </div>
        <p style="color:#6B5E4E; font-size:0.88rem; font-style:italic; margin-bottom:0.8rem;">
            {irr.get('adjustment_reason','')}
        </p>
        <div class="stat-row">
            <span class="stat-label">Volumen base</span>
            <span class="stat-value">{irr.get('base_liters','—')} L/m²</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Multiplicador suelo</span>
            <span class="stat-value">×{irr.get('soil_multiplier',1.0)}</span>
        </div>
        {assumed_html}
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── Fila 2: Estado cultivo + Prevención ───────────────────────────────────────
col_crop, col_prev = st.columns([1, 2])

with col_crop:
    assumed_note = " <span style='font-size:0.75rem;color:#9B8E7E;'>(estimada)</span>" \
                   if crop.get("assumed") else ""
    st.markdown(f"""
    <div class="card">
        <div class="card-title">🌱 Estado del cultivo</div>
        <div class="fase-badge">{str(crop.get('phase','—')).capitalize()}</div>
        {assumed_note}
        <p style="color:#4A3728; font-size:0.9rem; line-height:1.7; margin-top:0.5rem;">
            {crop.get('recommendation','')}
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_prev:
    priority_conf = {
        "alta":  ("prev-alta",  "🔴"),
        "media": ("prev-media", "🟡"),
        "baja":  ("prev-baja",  "🟢"),
    }
    st.markdown("""
    <div class="card-title" style="margin-bottom:0.8rem;">⚠️ Prevención y alertas</div>
    """, unsafe_allow_html=True)

    if prev:
        for item in prev:
            prio = str(item.get("priority", "baja")).lower()
            css, emoji = priority_conf.get(prio, ("prev-baja", "⚪"))
            st.markdown(f"""
            <div class="prev-item {css}">
                <span style="font-size:1.1rem;">{emoji}</span>
                <div>
                    <div style="font-weight:600; font-size:0.9rem; margin-bottom:0.2rem;">
                        {item.get('label','—')}
                        <span style="font-weight:400; font-size:0.78rem; color:#6B5E4E;">
                            · prioridad {prio}
                        </span>
                    </div>
                    <div style="font-size:0.85rem; color:#4A3728; line-height:1.5;">
                        {item.get('action','')}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="prev-item prev-baja">
            🟢 Sin alertas de prevención activas.
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── Explicación del agente ────────────────────────────────────────────────────
st.markdown("""
<div class="card-title" style="font-size:1.1rem; margin-bottom:0.8rem;">
    🧠 Explicación del sistema
</div>
""", unsafe_allow_html=True)

tab_plan, tab_agente, tab_alt = st.tabs([
    "📋 Plan detallado", "🤖 Agente de explicación", "🔀 Alternativas"
])

with tab_plan:
    st.markdown(
        f"<div style='line-height:1.8; font-size:0.95rem; padding:0.5rem 0;'>"
        f"{plan.get('explanation', 'Sin explicación disponible.')}</div>",
        unsafe_allow_html=True
    )

with tab_agente:
    if exp.get("summary"):
        st.markdown(exp["summary"])
        conf = exp.get("confidence", {})
        if conf:
            conf_color = {"alta": "#3B6B2A", "media": "#C8832A",
                          "baja": "#C0392B"}.get(conf.get("label",""), "#6B5E4E")
            st.markdown(f"""
            <div style="display:inline-flex; align-items:center; gap:0.5rem;
                        background:#F5F0E8; border-radius:20px; padding:0.3rem 0.9rem;
                        margin-top:0.5rem;">
                <span style="font-size:0.8rem; color:#6B5E4E;">Confianza:</span>
                <span style="font-weight:600; color:{conf_color};">
                    {conf.get('label','—')} ({conf.get('score','—')})
                </span>
            </div>
            """, unsafe_allow_html=True)
            if conf.get("reasons"):
                st.caption("Factores: " + ", ".join(conf["reasons"]))
    else:
        st.info("El agente de explicación no generó resumen en este análisis.")

with tab_alt:
    alternatives = exp.get("alternatives", [])
    if alternatives:
        for i, alt in enumerate(alternatives, 1):
            utility   = alt.get("utility")
            util_text = f"{utility:.2f}" if isinstance(utility, (int, float)) else "—"
            with st.expander(f"Alternativa {i} — utilidad {util_text}"):
                st.caption(alt.get("tradeoff", ""))
                for action in alt.get("actions", []):
                    st.markdown(f"- {str(action).replace('_',' ').capitalize()}")
    else:
        st.info("No hay escenarios alternativos disponibles.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<hr class='divider'>
<div style="text-align:center; color:#9B8E7E; font-size:0.78rem; padding-bottom:1rem;">
    AgroVid · Sistema de apoyo a la decisión vitícola · TFG CUNEF Universidad 2025–2026
</div>
""", unsafe_allow_html=True)