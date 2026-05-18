from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import logging

import streamlit as st

from web.auth import login_user, register_user, update_user_preferences
from web.db import init_db

@st.cache_data(show_spinner=False)
def load_stations():
    """Carga todas las estaciones AEMET y las devuelve como lista de opciones."""
    try:
        from tools.aemet_stations import get_stations
        df = get_stations()
        # Formato: "Nombre - Provincia (CODIGO)"
        opciones = {
            row["id"]: f"{row['nombre'].title()} - {row['provincia'].title()} ({row['id']})"
            for _, row in df.iterrows()
        }
        return opciones
    except Exception:
        return {"9995Y": "Pamplona / Noain - Navarra (9995Y)"}

def get_ccaa_from_station(station_id: str) -> str:
    """Devuelve la CCAA a partir del código de estación."""
    try:
        from tools.aemet_stations import station_to_ccaa
        return station_to_ccaa(station_id) or "Desconocida"
    except Exception:
        return "Desconocida"

logger = logging.getLogger(__name__)

# ── Configuracion de pagina ──────────────────────────────────────────────────
st.set_page_config(
    page_title="AgroVid · Gestion Inteligente del Vinedo",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS global ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --verde-vid:    #3B6B2A;
    --verde-claro:  #5A8F45;
    --tierra:       #8B5E3C;
    --ocre:         #C8832A;
    --crema:        #F5F0E8;
    --blanco:       #FDFCF9;
    --gris-suave:   #E8E2D9;
    --texto:        #2C2416;
    --texto-suave:  #6B5E4E;
    --rojo-alerta:  #C0392B;
    --amarillo:     #D4A017;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: var(--texto);
    background-color: var(--blanco);
}

h1, h2, h3 {
    font-family: 'Playfair Display', serif;
}

.stApp { background-color: var(--blanco); }

[data-testid="stSidebar"] {
    background-color: var(--verde-vid) !important;
    border-right: none;
}
[data-testid="stSidebar"] * { color: var(--crema) !important; }

.stButton > button {
    background-color: var(--verde-vid) !important;
    color: var(--crema) !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.5rem !important;
    transition: background-color 0.2s ease !important;
}
.stButton > button:hover { background-color: var(--verde-claro) !important; }

.stTabs [data-baseweb="tab-list"] {
    background-color: var(--crema);
    border: 1.5px solid var(--gris-suave);
    border-radius: 12px;
    padding: 6px;
    gap: 6px;
    margin-bottom: 1.5rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    color: var(--texto-suave) !important;
    padding: 0.5rem 1.2rem !important;
    border: 1px solid transparent !important;
    transition: all 0.2s !important;
}
.stTabs [data-baseweb="tab"]:hover {
    border-color: var(--gris-suave) !important;
    background-color: white !important;
}
.stTabs [aria-selected="true"] {
    background-color: var(--verde-vid) !important;
    color: white !important;
    border-color: var(--verde-vid) !important;
    font-weight: 600 !important;
}

[data-testid="metric-container"] {
    background-color: var(--crema);
    border: 1px solid var(--gris-suave);
    border-radius: 12px;
    padding: 1rem 1.2rem;
}
[data-testid="metric-container"] label {
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--texto-suave) !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif !important;
    font-size: 1.8rem !important;
    color: var(--verde-vid) !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid var(--gris-suave) !important;
    border-radius: 12px !important;
    background-color: var(--crema) !important;
    padding: 0.5rem !important;
}

.stTextInput input, .stSelectbox select {
    border: 1.5px solid var(--gris-suave) !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
}

.alerta-critica {
    background: linear-gradient(135deg, #FFF5F5, #FFE8E8);
    border-left: 4px solid var(--rojo-alerta);
    border-radius: 0 10px 10px 0;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
}
.alerta-media {
    background: linear-gradient(135deg, #FFFBF0, #FFF3D0);
    border-left: 4px solid var(--amarillo);
    border-radius: 0 10px 10px 0;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
}
.alerta-baja {
    background: linear-gradient(135deg, #F0FFF4, #E0F5E8);
    border-left: 4px solid var(--verde-claro);
    border-radius: 0 10px 10px 0;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
}

.sms-box {
    background: linear-gradient(135deg, var(--verde-vid), var(--verde-claro));
    color: white;
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    line-height: 1.6;
    letter-spacing: 0.01em;
    margin: 0.5rem 0;
}

.header-agrovid {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 0.5rem;
}
.header-agrovid h1 { margin: 0; font-size: 2rem; color: var(--verde-vid); }
.badge-region {
    background-color: var(--crema);
    border: 1px solid var(--gris-suave);
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.8rem;
    color: var(--texto-suave);
    font-weight: 500;
}

.divider-vid {
    border: none;
    border-top: 2px solid var(--gris-suave);
    margin: 1.5rem 0;
}

.historico-item {
    background-color: var(--crema);
    border: 1px solid var(--gris-suave);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
}

.stSpinner > div { border-top-color: var(--verde-vid) !important; }
</style>
""", unsafe_allow_html=True)


# ── Estado de sesion ─────────────────────────────────────────────────────────
def init_session() -> None:
    if "user"            not in st.session_state: st.session_state.user            = None
    if "analysis_result" not in st.session_state: st.session_state.analysis_result = None
    if "auth_screen"     not in st.session_state: st.session_state.auth_screen     = "login"


# ── CSS auth ──────────────────────────────────────────────────────────────────
AUTH_CSS = """
<style>
header[data-testid="stHeader"], footer, #MainMenu { display: none !important; }

[data-testid="stAppViewBlockContainer"],
[data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: 100% !important; }

.auth-img-panel {
    background-image: url('https://images.unsplash.com/photo-1506377247377-2a5b3b417ebb?w=1200&auto=format&fit=crop&q=80');
    background-size: cover;
    background-position: center;
    min-height: 100vh;
    position: relative;
}
.auth-img-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(170deg, rgba(20,50,10,0.25) 0%, rgba(10,30,5,0.60) 100%);
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    padding: 2.5rem 2.8rem;
}
.auth-tagline-img {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem;
    font-style: italic;
    color: rgba(245,240,232,0.93);
    line-height: 1.65;
    max-width: 320px;
}

.auth-logo-text {
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    font-weight: 700;
    color: #2C2416;
    line-height: 1;
    margin-bottom: 0.25rem;
}
.auth-tagline { font-size: 0.85rem; color: #6B5E4E; margin-bottom: 2.2rem; }
.auth-section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: #2C2416;
    margin-bottom: 1.4rem;
}
.auth-label {
    font-size: 0.8rem;
    font-weight: 500;
    color: #4A3728;
    margin-bottom: 0.3rem;
    display: block;
}
.auth-divider { border: none; border-top: 1px solid #D8D0C4; margin: 1.6rem 0; }
.auth-section-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: #9B8E7E;
    margin: 1.2rem 0 0.8rem;
}
</style>
"""


def _left_panel_html() -> str:
    return """
    <div class="auth-img-panel">
        <div class="auth-img-overlay">
            <div class="auth-tagline-img">
                Gestion inteligente del vinedo con IA Agentica
            </div>
        </div>
    </div>
    """


# ── Login ─────────────────────────────────────────────────────────────────────
def render_login() -> None:
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    col_img, col_form = st.columns([1, 1], gap="small")

    with col_img:
        st.markdown(_left_panel_html(), unsafe_allow_html=True)

    with col_form:
        st.markdown("<div style='height:20vh'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="auth-logo-text">AgroVid</div>
        <div class="auth-tagline">Gestion inteligente del vinedo con IA Agentica</div>
        <div class="auth-section-title">Iniciar sesion</div>
        """, unsafe_allow_html=True)

        st.markdown('<label class="auth-label">Correo electronico</label>', unsafe_allow_html=True)
        email = st.text_input("email_h", key="login_email", placeholder="tu@email.com", label_visibility="collapsed")

        st.markdown('<label class="auth-label">Contrasena</label>', unsafe_allow_html=True)
        password = st.text_input("pass_h", type="password", key="login_pass", placeholder="••••••••", label_visibility="collapsed")

        if st.button("Iniciar sesion", use_container_width=True, key="btn_login"):
            if email and password:
                user = login_user(email, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Correo o contrasena incorrectos.")
            else:
                st.warning("Completa todos los campos.")

        col_c = st.columns([1, 2, 1])
        with col_c[1]:
            if st.button("Olvidaste tu contrasena?", key="btn_forgot", use_container_width=True):
                st.session_state.auth_screen = "forgot"
                st.rerun()

        st.markdown("<hr class='auth-divider'>", unsafe_allow_html=True)
        if st.button("Crear nueva cuenta", use_container_width=True, key="btn_to_register"):
            st.session_state.auth_screen = "register"
            st.rerun()


# ── Olvide contrasena ─────────────────────────────────────────────────────────
def render_forgot_password() -> None:
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    col_img, col_form = st.columns([1, 1], gap="small")

    with col_img:
        st.markdown(_left_panel_html(), unsafe_allow_html=True)

    with col_form:
        st.markdown("<div style='height:22vh'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="auth-logo-text">AgroVid</div>
        <div class="auth-tagline">Recuperacion de contrasena</div>
        <div class="auth-section-title">Recuperar acceso</div>
        <p style="font-size:0.87rem; color:#6B5E4E; margin-bottom:1.5rem; line-height:1.65;">
            Introduce tu correo electronico y te enviaremos un enlace
            para restablecer tu contrasena.
        </p>
        """, unsafe_allow_html=True)

        st.markdown('<label class="auth-label">Correo electronico</label>', unsafe_allow_html=True)
        forgot_email = st.text_input("forgot_h", key="forgot_email", placeholder="tu@email.com", label_visibility="collapsed")

        if st.button("Enviar enlace de recuperacion", use_container_width=True, key="btn_send_link"):
            if forgot_email and "@" in forgot_email:
                st.success(f"Si existe una cuenta asociada a {forgot_email}, recibiras el enlace en breve.")
            else:
                st.error("Introduce un correo electronico valido.")

        st.markdown("<hr class='auth-divider'>", unsafe_allow_html=True)
        if st.button("Volver al inicio de sesion", key="btn_back_login"):
            st.session_state.auth_screen = "login"
            st.rerun()


# ── Registro ──────────────────────────────────────────────────────────────────
def render_register() -> None:
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    col_img, col_form = st.columns([1, 1], gap="small")

    with col_img:
        st.markdown(_left_panel_html(), unsafe_allow_html=True)

    with col_form:
        st.markdown("<div style='height:5vh'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="auth-logo-text">AgroVid</div>
        <div class="auth-tagline">Gestion inteligente del vinedo con IA Agentica</div>
        <div class="auth-section-title">Crear nueva cuenta</div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="auth-section-label">Datos de acceso</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<label class="auth-label">Correo electronico</label>', unsafe_allow_html=True)
            reg_email = st.text_input("reg_email_h", key="reg_email", placeholder="tu@email.com", label_visibility="collapsed")
        with c2:
            st.markdown('<label class="auth-label">Contrasena</label>', unsafe_allow_html=True)
            reg_password = st.text_input("reg_pass_h", type="password", key="reg_pass", placeholder="Minimo 8 caracteres", label_visibility="collapsed")

        st.markdown('<div class="auth-section-label">Tu vinedo</div>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            st.markdown('<label class="auth-label">Estacion meteorologica</label>', unsafe_allow_html=True)
            stations = load_stations()
            station_ids = list(stations.keys())
            default_idx = station_ids.index("9995Y") if "9995Y" in station_ids else 0
            selected_station = st.selectbox(
                "reg_st_h", options=station_ids, index=default_idx,
                format_func=lambda x: stations.get(x, x),
                key="reg_station", label_visibility="collapsed"
            )
            station = selected_station
            ccaa = get_ccaa_from_station(station)
            st.caption(f"Region detectada: {ccaa}")
            st.markdown('<label class="auth-label">Variedad de uva</label>', unsafe_allow_html=True)
            variety_opts = ["Usar la predominante de mi region"] + ['Airen', 'AlbarinBlanco', 'Albariño', 'Bobal', 'Garnacha', 'Godello', 'ListanBlancodeCanarias', 'Macabeo', 'MantoNegro', 'Mencia', 'Monastrell', 'Palomino', 'Pardina', 'PedroXimenez', 'Tempranillo', 'Verdejo']
            variety_sel = st.selectbox(
                "reg_var_h", options=variety_opts,
                index=0,
                key="reg_variety", label_visibility="collapsed"
            )
            variety = "" if variety_sel == "Usar la predominante de mi region" else variety_sel
            if variety_sel == "Usar la predominante de mi region":
                st.caption("Se usara la variedad predominante de tu region")
        with c4:
            st.markdown('<label class="auth-label">Tipo de suelo</label>', unsafe_allow_html=True)
            soil_type_opts = ["Usar el predominante de mi region"] + ['arenoso', 'franco', 'arcilloso', 'pizarra', 'volcanico', 'granitico', 'aluvial', 'calizo']
            soil_sel = st.selectbox("reg_soil_h", key="reg_soil",
                                     options=soil_type_opts,
                                     format_func=lambda x: x.capitalize(),
                                     label_visibility="collapsed")
            soil_type = "" if soil_sel == "Usar el predominante de mi region" else soil_sel
            if soil_sel == "Usar el predominante de mi region":
                st.caption("Se usara el suelo predominante de la variedad seleccionada")
            st.markdown('<label class="auth-label">Objetivo de produccion</label>', unsafe_allow_html=True)
            objective = st.selectbox("reg_obj_h", key="reg_obj",
                                     options=["equilibrio", "produccion", "calidad"],
                                     format_func=str.capitalize,
                                     label_visibility="collapsed")

        if st.button("Crear cuenta", use_container_width=True, key="btn_register"):
            if reg_email and reg_password:
                ok, msg = register_user(
                    email=reg_email, password=reg_password,
                    station=station, ccaa=ccaa, variety=variety,
                    soil_type=soil_type, objective=objective,
                )
                if ok:
                    st.success("Cuenta creada. Ya puedes iniciar sesion.")
                    st.session_state.auth_screen = "login"
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("El correo y la contrasena son obligatorios.")

        st.markdown("<hr class='auth-divider'>", unsafe_allow_html=True)
        if st.button("Volver al inicio de sesion", key="btn_back_from_register"):
            st.session_state.auth_screen = "login"
            st.rerun()


def render_auth() -> None:
    if "auth_screen" not in st.session_state:
        st.session_state.auth_screen = "login"
    screen = st.session_state.auth_screen
    if screen == "login":       render_login()
    elif screen == "forgot":    render_forgot_password()
    elif screen == "register":  render_register()


# ── Analisis inicial automatico ──────────────────────────────────────────────
def maybe_run_default_analysis(user: dict) -> None:
    if st.session_state.analysis_result is not None:
        return

    end   = date.today() - timedelta(days=8)
    start = date.today() - timedelta(days=13)

    try:
        from web.runner import run_analysis, save_analysis
    except Exception as e:
        st.error("No se pudo cargar el motor de analisis.")
        logger.error("Error importando runner: %s", e)
        return

    with st.spinner("Analizando tu vinedo..."):
        try:
            result = run_analysis(
                station=user["station"],
                ccaa=user["ccaa"],
                variety=user["variety"],
                start_date=start,
                end_date=end,
                objective=user.get("objective", "equilibrio"),
            )
            st.session_state.analysis_result = result
            save_analysis(user["id"], result)
        except Exception as e:
            logger.error("Error en analisis inicial: %s", e)
            st.error(
                "No se pudieron obtener datos meteorologicos para el periodo seleccionado. "
                "Prueba a ajustar las fechas en la pestana Configuracion."
            )
            st.stop()


# ── Header ────────────────────────────────────────────────────────────────────
def render_header(result: dict) -> None:
    meta = result.get("meta", {})
    obj  = meta.get("objective", "equilibrio").capitalize()
    st.markdown(f"""
    <div class="header-agrovid">
        <h1>AgroVid</h1>
        <span class="badge-region">{meta.get('ccaa','—')}</span>
        <span class="badge-region">{meta.get('station','—')}</span>
        <span class="badge-region">{meta.get('variety','—')}</span>
        <span class="badge-region">Objetivo: {obj}</span>
    </div>
    <p style="color:#6B5E4E; margin-bottom:1.2rem; font-size:0.88rem;">
        Periodo analizado: {meta.get('start_date','—')} a {meta.get('end_date','—')}
    </p>
    """, unsafe_allow_html=True)


# ── Tab 1: Inicio ─────────────────────────────────────────────────────────────
def tab_principal(result: dict) -> None:
    summary  = result.get("summary", "Sin resumen disponible.")
    risks    = result.get("risk_explanation", [])
    sms_text = result.get("sms_text", "")

    with st.container(border=True):
        st.markdown("#### Resumen ejecutivo")
        st.markdown(f"<p style='font-size:1.05rem; line-height:1.7;'>{summary}</p>",
                    unsafe_allow_html=True)

    st.markdown("<div class='divider-vid'></div>", unsafe_allow_html=True)

    st.markdown("#### Estado del vinedo")
    priority_map = {
        "critico": ("alerta-critica", "Critico"),
        "alto":    ("alerta-critica", "Alto"),
        "medio":   ("alerta-media",   "Medio"),
        "bajo":    ("alerta-baja",    "Bajo"),
    }
    if risks:
        cols = st.columns(min(len(risks), 3))
        for i, risk in enumerate(risks[:3]):
            level = risk.get("level", "bajo")
            if hasattr(level, "value"): level = level.value
            css_class, label = priority_map.get(str(level).lower(), ("alerta-baja", "Bajo"))
            with cols[i]:
                st.markdown(f"""
                <div class="{css_class}">
                    <div style="font-weight:600; font-size:0.92rem; margin-bottom:0.3rem;">
                        {risk.get('type','Riesgo').replace('_',' ').capitalize()}
                    </div>
                    <div style="font-size:0.82rem; color:#4A3728;">
                        Nivel: <strong>{label}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="alerta-baja">
            <strong>Sin alertas activas</strong> — condiciones favorables para el cultivo.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='divider-vid'></div>", unsafe_allow_html=True)

    st.markdown("#### Notificacion SMS")
    if sms_text:
        st.markdown(f"""
        <div class="sms-box">{sms_text.replace(chr(10),'<br>')}</div>
        <div style="font-size:0.75rem; color:#6B5E4E; margin-top:0.3rem; text-align:right;">
            {len(sms_text)}/160 caracteres
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("SMS no disponible.")

    st.markdown("<div class='divider-vid'></div>", unsafe_allow_html=True)

    st.markdown("#### Analisis recientes")
    try:
        from web.runner import get_last_analyses
        rows = get_last_analyses(st.session_state.user["id"], limit=5)
    except Exception as e:
        logger.error("Error cargando historico: %s", e)
        st.error("No se pudo cargar el historico.")
        return
    if not rows:
        st.caption("Aun no hay analisis guardados.")
        return
    for row in rows:
        st.markdown(f"""
        <div class="historico-item">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:500; font-size:0.9rem;">
                    {row['ccaa']} · {row['variety']}
                </span>
                <span style="font-size:0.8rem; color:#6B5E4E;">
                    {row['start_date']} a {row['end_date']}
                </span>
            </div>
            <div style="font-size:0.82rem; color:#6B5E4E; margin-top:0.3rem;">
                {row['summary'][:200] + ('...' if len(row['summary']) > 200 else '')}
            </div>
            <div style="font-size:0.75rem; color:#9B8E7E; margin-top:0.2rem;">
                {row['created_at']}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Tab 2: Riesgos ────────────────────────────────────────────────────────────
def tab_riesgos(result: dict) -> None:
    risks = result.get("risk_explanation", [])
    priority_map = {
        "critico": ("alerta-critica", "Critico"),
        "alto":    ("alerta-critica", "Alto"),
        "medio":   ("alerta-media",   "Medio"),
        "bajo":    ("alerta-baja",    "Bajo"),
    }

    if not risks:
        st.markdown("""
        <div class="alerta-baja" style="margin-top:1rem;">
            <strong>No se han detectado riesgos significativos</strong> en el periodo analizado.
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"**{len(risks)} riesgo(s) detectado(s)** en el periodo de analisis.")

    for risk in risks:
        level = risk.get("level", "bajo")
        if hasattr(level, "value"): level = level.value
        css_class, label = priority_map.get(str(level).lower(), ("alerta-baja", "Bajo"))

        with st.expander(
            f"{risk.get('type','Riesgo').replace('_',' ').capitalize()} — nivel {label}",
            expanded=(str(level).lower() in ("alto", "critico"))
        ):
            col_info, col_detalle = st.columns([1, 2])
            with col_info:
                st.markdown(f"""
                <div class="{css_class}" style="margin:0;">
                    <div style="font-size:0.8rem; color:#4A3728;">
                        <strong>Nivel:</strong> {label}<br>
                        <strong>Valor observado:</strong> {risk.get('value','—')}<br>
                        <strong>Umbral:</strong> {risk.get('threshold','—')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_detalle:
                causes = risk.get("causes", [])
                if causes:
                    st.markdown("**Causas:**")
                    for c in causes[:3]:
                        cond    = f" ({c.get('condition','')})" if isinstance(c, dict) and c.get("condition") else ""
                        label_c = c.get('label','—') if isinstance(c, dict) else str(c)
                        st.markdown(f"- {label_c}{cond}")

                effects = risk.get("effects", [])
                if effects:
                    st.markdown("**Efectos sobre la vid:**")
                    for e in effects[:3]:
                        if isinstance(e, dict):
                            relacion = e.get('relation', 'afecta a')
                            label_e  = e.get('label', '—')
                            st.markdown(f"- {relacion.capitalize()} {label_e.lower()}")
                        else:
                            st.markdown(f"- {str(e)}")

                actions = risk.get("recommended_actions", [])
                if actions:
                    st.markdown("**Acciones recomendadas:**")
                    for a in actions[:2]:
                        cond    = f" ({a.get('condition','')})" if isinstance(a, dict) and a.get("condition") else ""
                        label_a = a.get('label','—') if isinstance(a, dict) else str(a)
                        st.markdown(f"- {label_a}{cond}")

    alternatives = result.get("alternatives", [])
    if alternatives:
        st.markdown("<div class='divider-vid'></div>", unsafe_allow_html=True)
        st.markdown("#### Escenarios alternativos evaluados")
        alt_cols = st.columns(len(alternatives[:2]))
        for i, alt in enumerate(alternatives[:2]):
            utility   = alt.get("utility")
            util_text = f"{utility:.2f}" if isinstance(utility, (int, float)) else "—"
            with alt_cols[i]:
                with st.container(border=True):
                    st.markdown(f"**Opcion {i+1}** · Utilidad: `{util_text}`")
                    acciones = alt.get("actions", [])
                    traduccion = {
                        "light": "ligero", "moderate": "moderado", "intensive": "intensivo",
                        "preventive": "preventivo", "curative": "curativo",
                        "early": "anticipado", "delayed": "retrasado", "normal": "normal",
                        "light defoliation": "deshojado ligero", "heavy defoliation": "deshojado intenso",
                        "none": "ninguno", "irrigation": "riego", "fungicide": "fungicida",
                        "harvest timing": "calendario vendimia", "canopy management": "manejo dosel",
                    }
                    for a in acciones:
                        texto = str(a).replace("_", " ")
                        for en, es in traduccion.items():
                            texto = texto.replace(en, es)
                        st.markdown(f"- {texto.capitalize()}")


# ── Tab 3: Plan diario ────────────────────────────────────────────────────────
def tab_plan_diario(result: dict) -> None:
    import re
    plan_text = result.get("daily_plan_text", "")
    reasoning = result.get("recommendation_reasoning", "")

    if plan_text:
        plan_text = re.sub(
            r'(\d+\.\d{3,})\s*%',
            lambda m: f"{float(m.group(1)):.2f} %",
            plan_text
        )

    st.markdown("#### Plan de actuacion recomendado")
    if plan_text:
        secciones = plan_text.split("\n\n")
        for seccion in secciones:
            if seccion.strip():
                st.markdown(f"""
                <div style="background:#F5F0E8; border-radius:10px; padding:1rem 1.2rem;
                            line-height:1.8; font-size:0.95rem; margin-bottom:0.8rem;
                            border: 1px solid #E8E2D9;">
                    {seccion.strip().replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Plan diario no disponible.")

    if reasoning:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        with st.expander("Justificacion de la recomendacion"):
            st.markdown(f"""
            <div style="line-height:1.8; font-size:0.93rem; color:#2C2416;">
                {reasoning}
            </div>
            """, unsafe_allow_html=True)


# ── Tab 4: Audio ──────────────────────────────────────────────────────────────
def tab_audio(result: dict) -> None:
    summary  = result.get("summary", "")
    sms_text = result.get("sms_text", "")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("#### Escuchar recomendacion")
        texto_audio = st.radio(
            "Que quieres escuchar?",
            options=["Resumen ejecutivo", "Texto SMS"],
            horizontal=True,
        )
        contenido = summary if texto_audio == "Resumen ejecutivo" else sms_text

        if contenido:
            with st.container(border=True):
                st.markdown(f"""
                <p style="font-size:0.92rem; line-height:1.7; color:#2C2416;">
                    {contenido}
                </p>
                """, unsafe_allow_html=True)

        if st.button("Generar audio", use_container_width=True):
            if not contenido:
                st.warning("No hay texto disponible para generar el audio.")
            else:
                try:
                    from web.voice import generate_voice_file
                    with st.spinner("Generando audio..."):
                        audio_path = generate_voice_file(contenido)
                    if audio_path and Path(audio_path).exists():
                        st.audio(Path(audio_path).read_bytes(), format="audio/mp3")
                        st.success("Audio generado correctamente.")
                    else:
                        st.warning("No se pudo generar el audio.")
                except Exception as e:
                    logger.error("Error generando audio: %s", e)
                    st.error("No se pudo generar el audio.")

    with col_right:
        st.markdown("#### Texto completo")
        st.markdown(f"""
        <div style="background:#F5F0E8; border-radius:12px; padding:1.2rem;
                    font-size:0.9rem; line-height:1.8; color:#2C2416;
                    border: 1px solid #E8E2D9; min-height:200px;">
            {summary or 'Sin resumen disponible.'}
        </div>
        """, unsafe_allow_html=True)


# ── Tab 5: Configuracion ──────────────────────────────────────────────────────
def tab_configuracion(user: dict) -> dict:
    st.markdown("#### Configuracion del analisis")

    today         = date.today()
    default_end   = today - timedelta(days=5)
    default_start = today - timedelta(days=10)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Localizacion y cultivo**")
        stations = load_stations()
        station_ids = list(stations.keys())
        current_station = user.get("station", "9995Y")
        default_idx = station_ids.index(current_station) if current_station in station_ids else 0
        station = st.selectbox(
            "Estacion meteorologica", options=station_ids, index=default_idx,
            format_func=lambda x: stations.get(x, x),
        )
        ccaa = get_ccaa_from_station(station)
        st.caption(f"Region detectada: {ccaa}")
        var_opts = ["Usar la predominante de mi region"] + ['Airen', 'AlbarinBlanco', 'Albariño', 'Bobal', 'Garnacha', 'Godello', 'ListanBlancodeCanarias', 'Macabeo', 'MantoNegro', 'Mencia', 'Monastrell', 'Palomino', 'Pardina', 'PedroXimenez', 'Tempranillo', 'Verdejo']
        current_var = user.get("variety", "")
        var_idx = var_opts.index(current_var) if current_var in var_opts else 0
        variety_sel_cfg = st.selectbox("Variedad de uva", options=var_opts, index=var_idx)
        variety = "" if variety_sel_cfg == "Usar la predominante de mi region" else variety_sel_cfg
        if variety_sel_cfg == "Usar la predominante de mi region":
            st.caption("Se usara la variedad predominante de tu region")

    with col2:
        st.markdown("**Caracteristicas del vinedo**")
        soil_opts_cfg = ["Usar el predominante de mi region"] + ['arenoso', 'franco', 'arcilloso', 'pizarra', 'volcanico', 'granitico', 'aluvial', 'calizo']
        current_soil = user.get("soil_type", "")
        soil_idx = soil_opts_cfg.index(current_soil) if current_soil in soil_opts_cfg else 0
        soil_sel_cfg = st.selectbox(
            "Tipo de suelo", options=soil_opts_cfg,
            index=soil_idx,
            format_func=lambda x: x.capitalize()
        )
        soil_type = "" if soil_sel_cfg == "Usar el predominante de mi region" else soil_sel_cfg
        if soil_sel_cfg == "Usar el predominante de mi region":
            st.caption("Se usara el suelo predominante de la variedad seleccionada")
        obj_opts  = ["equilibrio", "produccion", "calidad"]
        objective = st.selectbox(
            "Objetivo de produccion", options=obj_opts,
            index=obj_opts.index(user.get("objective", "equilibrio")),
            format_func=str.capitalize
        )
        st.caption(
            "Calidad: prioriza concentracion y aromas. "
            "Produccion: maximiza rendimiento. "
            "Equilibrio: balance entre ambos."
        )

    st.markdown("**Periodo de analisis**")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Fecha de inicio", value=default_start)
    with col_d2:
        end_date   = st.date_input("Fecha de fin",    value=default_end)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    col_save, col_recalc, _ = st.columns([1, 1, 2])

    save_prefs = col_save.button("Guardar preferencias",  use_container_width=True)
    recalc     = col_recalc.button("Recalcular analisis", use_container_width=True, type="primary")

    if save_prefs:
        update_user_preferences(
            user_id=user["id"], station=station, ccaa=ccaa,
            variety=variety, soil_type=soil_type, objective=objective,
        )
        st.session_state.user = {
            **user, "station": station, "ccaa": ccaa,
            "variety": variety, "soil_type": soil_type,
            "objective": objective,
        }
        st.session_state.analysis_result = None
        st.success("Preferencias guardadas. El analisis se recalculara automaticamente.")
        st.rerun()

    st.markdown("<div class='divider-vid'></div>", unsafe_allow_html=True)
    st.markdown("#### Informacion de la cuenta")
    st.markdown(f"""
    <div style="background:#F5F0E8; border-radius:10px; padding:1rem 1.2rem;
                border: 1px solid #E8E2D9;">
        <div style="font-size:0.9rem; color:#6B5E4E;">
            <strong>Email:</strong> {user.get('email','—')}<br>
            <strong>Region:</strong> {user.get('ccaa','—')}<br>
            <strong>Variedad:</strong> {user.get('variety','—')}<br>
            <strong>Objetivo:</strong> {user.get('objective','equilibrio').capitalize()}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Cerrar sesion", use_container_width=False):
        st.session_state.user = None
        st.session_state.analysis_result = None
        st.rerun()

    return {
        "station": station, "ccaa": ccaa, "variety": variety,
        "soil_type": soil_type, "objective": objective,
        "start_date": start_date, "end_date": end_date,
        "recalc": recalc,
    }


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    init_db()
    init_session()

    if st.session_state.user is None:
        render_auth()
        return

    user = st.session_state.user
    maybe_run_default_analysis(user)
    result = st.session_state.analysis_result

    if result:
        render_header(result)

    t1, t2, t3, t4, t5 = st.tabs([
        "Inicio",
        "Riesgos",
        "Plan diario",
        "Escuchar",
        "Configuracion",
    ])

    with t1:
        tab_principal(result) if result else st.info("Calculando el analisis inicial...")
    with t2:
        tab_riesgos(result)   if result else st.info("El analisis aun no esta disponible.")
    with t3:
        tab_plan_diario(result) if result else st.info("El analisis aun no esta disponible.")
    with t4:
        tab_audio(result)     if result else st.info("El analisis aun no esta disponible.")
    with t5:
        prefs = tab_configuracion(user)
        if prefs["recalc"]:
            try:
                from web.runner import run_analysis, save_analysis
                with st.spinner("Recalculando analisis..."):
                    new_result = run_analysis(
                        station=prefs["station"], ccaa=prefs["ccaa"],
                        variety=prefs["variety"],
                        start_date=prefs["start_date"],
                        end_date=prefs["end_date"],
                        objective=prefs["objective"],
                    )
                    st.session_state.analysis_result = new_result
                    save_analysis(user["id"], new_result)
                    st.success("Analisis actualizado.")
                    st.rerun()
            except Exception as e:
                logger.error("Error al recalcular analisis: %s", e)
                st.error(
                    "No se pudo completar el analisis. "
                    "Verifica la estacion AEMET y el periodo de fechas."
                )


if __name__ == "__main__":
    main()