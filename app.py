from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from web.auth import login_user, register_user, update_user_preferences
from web.db import init_db

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="AgroVid · Gestión Inteligente del Viñedo",
    page_icon="🍇",
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

/* Fondo general */
.stApp {
    background-color: var(--blanco);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: var(--verde-vid) !important;
    border-right: none;
}
[data-testid="stSidebar"] * {
    color: var(--crema) !important;
}
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stSelectbox select {
    background-color: rgba(255,255,255,0.12) !important;
    color: var(--crema) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 6px !important;
}

/* Botones principales */
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
.stButton > button:hover {
    background-color: var(--verde-claro) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: var(--gris-suave);
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    color: var(--texto-suave) !important;
}
.stTabs [aria-selected="true"] {
    background-color: var(--verde-vid) !important;
    color: white !important;
}

/* Métricas */
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

/* Contenedores con borde */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid var(--gris-suave) !important;
    border-radius: 12px !important;
    background-color: var(--crema) !important;
    padding: 0.5rem !important;
}

/* Inputs */
.stTextInput input, .stSelectbox select {
    border: 1.5px solid var(--gris-suave) !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput input:focus {
    border-color: var(--verde-vid) !important;
    box-shadow: 0 0 0 2px rgba(59,107,42,0.15) !important;
}

/* Alertas personalizadas */
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

/* SMS box */
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

/* Header personalizado */
.header-agrovid {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 0.5rem;
}
.header-agrovid h1 {
    margin: 0;
    font-size: 2rem;
    color: var(--verde-vid);
}
.badge-region {
    background-color: var(--crema);
    border: 1px solid var(--gris-suave);
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.8rem;
    color: var(--texto-suave);
    font-weight: 500;
}

/* Confianza */
.confianza-alta  { color: var(--verde-claro); font-weight: 600; }
.confianza-media { color: var(--ocre); font-weight: 600; }
.confianza-baja  { color: var(--rojo-alerta); font-weight: 600; }

/* Divider personalizado */
.divider-vid {
    border: none;
    border-top: 2px solid var(--gris-suave);
    margin: 1.5rem 0;
}

/* Histórico */
.historico-item {
    background-color: var(--crema);
    border: 1px solid var(--gris-suave);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
    transition: border-color 0.2s;
}
.historico-item:hover {
    border-color: var(--verde-vid);
}

/* Spinner personalizado */
.stSpinner > div {
    border-top-color: var(--verde-vid) !important;
}
</style>
""", unsafe_allow_html=True)


# ── Estado de sesión ─────────────────────────────────────────────────────────
def init_session() -> None:
    if "user" not in st.session_state:
        st.session_state.user = None
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "auth_screen" not in st.session_state:
        st.session_state.auth_screen = "login"


def logout() -> None:
    st.session_state.user = None
    st.session_state.analysis_result = None
    st.rerun()


# ── CSS pantallas de auth ─────────────────────────────────────────────────────
AUTH_CSS = """
<style>
header[data-testid="stHeader"],
footer,
#MainMenu { display: none !important; }

[data-testid="stAppViewBlockContainer"],
[data-testid="stMainBlockContainer"] {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Eliminar padding de columnas en auth */
.auth-col-img  > div:first-child { padding: 0 !important; }
.auth-col-form > div:first-child { padding: 0 !important; }

/* Imagen izquierda */
.auth-img-panel {
    background-image: url('https://images.unsplash.com/photo-1506377247377-2a5b3b417ebb?w=1200&auto=format&fit=crop&q=80');
    background-size: cover;
    background-position: center;
    min-height: 100vh;
    position: relative;
    border-radius: 0;
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
.auth-quote {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem;
    font-style: italic;
    color: rgba(245,240,232,0.93);
    line-height: 1.65;
    max-width: 320px;
}
.auth-quote-author {
    font-family: 'DM Sans', sans-serif;
    font-style: normal;
    font-size: 0.75rem;
    color: rgba(245,240,232,0.55);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 0.6rem;
}

/* Panel derecho — formulario */
.auth-form-panel {
    background-color: #F5F0E8;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 3rem 4rem;
}
.auth-inner {
    width: 100%;
    max-width: 400px;
}
.auth-logo-text {
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    font-weight: 700;
    color: #2C2416;
    line-height: 1;
    margin-bottom: 0.25rem;
}
.auth-tagline {
    font-size: 0.85rem;
    color: #6B5E4E;
    margin-bottom: 2.2rem;
}
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
.auth-input {
    width: 100%;
    padding: 0.65rem 0.9rem;
    border: 1.5px solid #D8D0C4;
    border-radius: 8px;
    background: #FDFCF9;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.92rem;
    color: #2C2416;
    outline: none;
    box-sizing: border-box;
    transition: border-color 0.2s;
    margin-bottom: 1rem;
}
.auth-input:focus { border-color: #3B6B2A; }
.auth-input::placeholder { color: #B0A49A; }

.auth-btn-primary {
    width: 100%;
    padding: 0.75rem;
    background-color: #4A3728;
    color: #F5F0E8;
    border: none;
    border-radius: 24px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
    margin-top: 0.3rem;
}
.auth-btn-primary:hover { background-color: #3B6B2A; }

.auth-btn-secondary {
    width: 100%;
    padding: 0.7rem;
    background: transparent;
    border: 1.5px solid #8B7A6A;
    border-radius: 24px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.92rem;
    color: #4A3728;
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;
}
.auth-btn-secondary:hover { border-color: #3B6B2A; color: #3B6B2A; }

.auth-link-btn {
    background: none;
    border: none;
    color: #5A4A3A;
    font-size: 0.83rem;
    cursor: pointer;
    text-decoration: underline;
    padding: 0;
    font-family: 'DM Sans', sans-serif;
    display: block;
    text-align: center;
    margin: 0.8rem auto 0;
}
.auth-divider {
    border: none;
    border-top: 1px solid #D8D0C4;
    margin: 1.6rem 0;
}
.auth-success {
    background: linear-gradient(135deg, #EAF5E3, #D4ECC8);
    border: 1px solid #5A8F45;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    text-align: center;
    margin-top: 1rem;
}
.auth-success-icon { font-size: 2rem; display: block; margin-bottom: 0.5rem; }
.auth-success p { color: #2C5A1A; font-size: 0.88rem; margin: 0; line-height: 1.6; }
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
            <div class="auth-quote">
                "El vino es la prueba de que Dios nos ama y quiere que seamos felices."
                <div class="auth-quote-author">— Benjamin Franklin</div>
            </div>
        </div>
    </div>
    """


# ── Pantalla login ─────────────────────────────────────────────────────────────
def render_login() -> None:
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    col_img, col_form = st.columns([1, 1], gap="small")

    with col_img:
        st.markdown(_left_panel_html(), unsafe_allow_html=True)

    with col_form:
        # Espaciado vertical para centrar
        st.markdown("<div style='height:20vh'></div>", unsafe_allow_html=True)

        # Logo y tagline
        st.markdown("""
        <div class="auth-logo-text">AgroVid</div>
        <div class="auth-tagline">Gestión inteligente del viñedo con IA Agéntica</div>
        <div class="auth-section-title">Iniciar sesión</div>
        """, unsafe_allow_html=True)

        # Campos con label HTML custom + input de Streamlit
        st.markdown('<label class="auth-label">Correo electrónico</label>',
                    unsafe_allow_html=True)
        email = st.text_input("email_hidden", key="login_email",
                              placeholder="tu@email.com",
                              label_visibility="collapsed")

        st.markdown('<label class="auth-label">Contraseña</label>',
                    unsafe_allow_html=True)
        password = st.text_input("pass_hidden", type="password", key="login_pass",
                                 placeholder="••••••••",
                                 label_visibility="collapsed")

        st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)

        if st.button("Iniciar sesión", use_container_width=True, key="btn_login"):
            if email and password:
                user = login_user(email, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Correo o contraseña incorrectos.")
            else:
                st.warning("Completa todos los campos.")

        # Link olvidé contraseña — centrado
        col_c = st.columns([1, 2, 1])
        with col_c[1]:
            if st.button("¿Olvidaste tu contraseña?", key="btn_forgot",
                         use_container_width=True):
                st.session_state.auth_screen = "forgot"
                st.rerun()

        st.markdown("<hr class='auth-divider'>", unsafe_allow_html=True)

        if st.button("Crear nueva cuenta", use_container_width=True,
                     key="btn_to_register"):
            st.session_state.auth_screen = "register"
            st.rerun()


# ── Pantalla olvidé contraseña ─────────────────────────────────────────────────
def render_forgot_password() -> None:
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    col_img, col_form = st.columns([1, 1], gap="small")

    with col_img:
        st.markdown(_left_panel_html(), unsafe_allow_html=True)

    with col_form:
        st.markdown("<div style='height:22vh'></div>", unsafe_allow_html=True)

        st.markdown("""
        <div class="auth-logo-text">AgroVid</div>
        <div class="auth-tagline">Recuperación de contraseña</div>
        <div class="auth-section-title">¿Olvidaste tu contraseña?</div>
        <p style="font-size:0.87rem; color:#6B5E4E; margin-bottom:1.5rem; line-height:1.65;">
            Introduce tu correo electrónico y te enviaremos un enlace
            para restablecer tu contraseña en los próximos minutos.
        </p>
        """, unsafe_allow_html=True)

        st.markdown('<label class="auth-label">Correo electrónico</label>',
                    unsafe_allow_html=True)
        forgot_email = st.text_input("forgot_hidden", key="forgot_email",
                                     placeholder="tu@email.com",
                                     label_visibility="collapsed")

        st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)

        if st.button("Enviar enlace de recuperación", use_container_width=True,
                     key="btn_send_link"):
            if forgot_email and "@" in forgot_email:
                st.markdown(f"""
                <div class="auth-success">
                    <span class="auth-success-icon">📧</span>
                    <p>Si existe una cuenta asociada a <strong>{forgot_email}</strong>,
                    recibirás un correo con el enlace para restablecer tu contraseña.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Introduce un correo electrónico válido.")

        st.markdown("<hr class='auth-divider'>", unsafe_allow_html=True)

        if st.button("← Volver al inicio de sesión", key="btn_back_login",
                     use_container_width=False):
            st.session_state.auth_screen = "login"
            st.rerun()


# ── Pantalla registro ──────────────────────────────────────────────────────────
def render_register() -> None:
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    col_img, col_form = st.columns([1, 1], gap="small")

    with col_img:
        st.markdown(_left_panel_html(), unsafe_allow_html=True)

    with col_form:
        st.markdown("<div style='height:5vh'></div>", unsafe_allow_html=True)

        st.markdown("""
        <div class="auth-logo-text">AgroVid</div>
        <div class="auth-tagline">Gestión inteligente del viñedo con IA Agéntica</div>
        <div class="auth-section-title">Crear nueva cuenta</div>
        """, unsafe_allow_html=True)

        # Datos de acceso
        st.markdown('<div class="auth-section-label">Datos de acceso</div>',
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<label class="auth-label">Correo electrónico</label>',
                        unsafe_allow_html=True)
            reg_email = st.text_input("reg_email_h", key="reg_email",
                                      placeholder="tu@email.com",
                                      label_visibility="collapsed")
        with c2:
            st.markdown('<label class="auth-label">Contraseña</label>',
                        unsafe_allow_html=True)
            reg_password = st.text_input("reg_pass_h", type="password", key="reg_pass",
                                         placeholder="Mínimo 8 caracteres",
                                         label_visibility="collapsed")

        # Datos del viñedo
        st.markdown('<div class="auth-section-label">Tu viñedo</div>',
                    unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            st.markdown('<label class="auth-label">Estación AEMET</label>',
                        unsafe_allow_html=True)
            station = st.text_input("reg_st_h", value="9995Y", key="reg_station",
                                    label_visibility="collapsed")
            st.markdown('<label class="auth-label">Comunidad autónoma</label>',
                        unsafe_allow_html=True)
            ccaa = st.text_input("reg_ccaa_h", value="Navarra", key="reg_ccaa",
                                 label_visibility="collapsed")
            st.markdown('<label class="auth-label">Variedad principal</label>',
                        unsafe_allow_html=True)
            variety = st.text_input("reg_var_h", value="Tempranillo", key="reg_variety",
                                    label_visibility="collapsed")
        with c4:
            st.markdown('<label class="auth-label">Tipo de suelo</label>',
                        unsafe_allow_html=True)
            soil_type = st.selectbox("reg_soil_h", key="reg_soil",
                                     options=["", "arenoso", "franco", "arcilloso"],
                                     format_func=lambda x: "Selecciona..." if x == "" else x.capitalize(),
                                     label_visibility="collapsed")
            st.markdown('<label class="auth-label">Sistema de riego</label>',
                        unsafe_allow_html=True)
            irrigation = st.selectbox("reg_irr_h", key="reg_irr",
                                      options=["", "goteo", "aspersión", "secano"],
                                      format_func=lambda x: "Selecciona..." if x == "" else x.capitalize(),
                                      label_visibility="collapsed")
            st.markdown('<label class="auth-label">Objetivo</label>',
                        unsafe_allow_html=True)
            objective = st.selectbox("reg_obj_h", key="reg_obj",
                                     options=["equilibrio", "producción", "calidad"],
                                     format_func=str.capitalize,
                                     label_visibility="collapsed")

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        if st.button("Crear cuenta", use_container_width=True, key="btn_register"):
            if reg_email and reg_password:
                ok, msg = register_user(
                    email=reg_email, password=reg_password,
                    station=station, ccaa=ccaa, variety=variety,
                    soil_type=soil_type, irrigation_system=irrigation,
                    objective=objective,
                )
                if ok:
                    st.success("✓ Cuenta creada. Ya puedes iniciar sesión.")
                    st.session_state.auth_screen = "login"
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("El correo y la contraseña son obligatorios.")

        st.markdown("<hr class='auth-divider'>", unsafe_allow_html=True)

        if st.button("← Volver al inicio de sesión", key="btn_back_from_register",
                     use_container_width=False):
            st.session_state.auth_screen = "login"
            st.rerun()


# ── Router de auth ─────────────────────────────────────────────────────────────
def render_auth() -> None:
    if "auth_screen" not in st.session_state:
        st.session_state.auth_screen = "login"
    screen = st.session_state.auth_screen
    if screen == "login":
        render_login()
    elif screen == "forgot":
        render_forgot_password()
    elif screen == "register":
        render_register()





# ── Análisis inicial automático ──────────────────────────────────────────────
def maybe_run_default_analysis(user: dict) -> None:
    if st.session_state.analysis_result is not None:
        return
    today = date.today()
    end   = today + timedelta(days=4)
    try:
        from web.runner import run_analysis, save_analysis
    except Exception as e:
        st.error(f"No se pudo cargar el motor de análisis: {e}")
        return
    with st.spinner("🌿 Analizando tu viñedo..."):
        try:
            result = run_analysis(
                station=user["station"], ccaa=user["ccaa"],
                variety=user["variety"], start_date=today, end_date=end,
            )
            st.session_state.analysis_result = result
            save_analysis(user["id"], result)
        except Exception as e:
            st.error(f"Error al calcular el análisis: {e}")


# ── Header compartido ────────────────────────────────────────────────────────
def render_header(result: dict) -> None:
    meta       = result.get("meta", {})
    confidence = result.get("confidence", {})
    conf_label = confidence.get("label", "")
    conf_class = {"alta": "confianza-alta", "media": "confianza-media",
                  "baja": "confianza-baja"}.get(conf_label, "")
    st.markdown(f"""
    <div class="header-agrovid">
        <h1>🍇 AgroVid</h1>
        <span class="badge-region">{meta.get('ccaa','—')}</span>
        <span class="badge-region">📍 {meta.get('station','—')}</span>
        <span class="badge-region">🌿 {meta.get('variety','—')}</span>
    </div>
    <p style="color:#6B5E4E; margin-bottom:1.2rem; font-size:0.88rem;">
        Periodo: {meta.get('start_date','—')} → {meta.get('end_date','—')} &nbsp;·&nbsp;
        Confianza: <span class="{conf_class}">{conf_label or 'N/D'}
        ({confidence.get('score','—')})</span>
    </p>
    """, unsafe_allow_html=True)


# ── Pestaña 1: Pantalla principal ─────────────────────────────────────────────
def tab_principal(result: dict) -> None:
    summary  = result.get("summary", "Sin resumen disponible.")
    risks    = result.get("risk_explanation", [])
    sms_text = result.get("sms_text", "")

    # Resumen ejecutivo
    with st.container(border=True):
        st.markdown("#### 📋 Resumen ejecutivo")
        st.markdown(f"<p style='font-size:1.05rem; line-height:1.7;'>{summary}</p>",
                    unsafe_allow_html=True)

    st.markdown("<div class='divider-vid'></div>", unsafe_allow_html=True)

    # Vista rápida de riesgos (máx. 3 en fila)
    st.markdown("#### ⚡ Estado del viñedo hoy")
    priority_map = {
        "crítico": ("alerta-critica", "🔴"),
        "alto":    ("alerta-critica", "🟠"),
        "medio":   ("alerta-media",   "🟡"),
        "bajo":    ("alerta-baja",    "🟢"),
    }
    if risks:
        cols = st.columns(min(len(risks), 3))
        for i, risk in enumerate(risks[:3]):
            level = risk.get("level", "bajo")
            if hasattr(level, "value"):
                level = level.value
            css_class, emoji = priority_map.get(str(level).lower(), ("alerta-baja", "⚪"))
            with cols[i]:
                st.markdown(f"""
                <div class="{css_class}">
                    <div style="font-weight:600; font-size:0.92rem; margin-bottom:0.3rem;">
                        {emoji} {risk.get('type','Riesgo').replace('_',' ').capitalize()}
                    </div>
                    <div style="font-size:0.82rem; color:#4A3728;">
                        Nivel: <strong>{level}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="alerta-baja">
            🟢 <strong>Sin alertas activas</strong> — condiciones favorables para el cultivo.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='divider-vid'></div>", unsafe_allow_html=True)

    # SMS preview
    st.markdown("#### 📱 Notificación SMS del día")
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

    # Histórico
    st.markdown("#### 🕐 Análisis recientes")
    try:
        from web.runner import get_last_analyses
        rows = get_last_analyses(st.session_state.user["id"], limit=5)
    except Exception as e:
        st.error(f"No se pudo cargar el histórico: {e}")
        return
    if not rows:
        st.caption("Aún no hay análisis guardados.")
        return
    for row in rows:
        st.markdown(f"""
        <div class="historico-item">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:500; font-size:0.9rem;">
                    📍 {row['ccaa']} · 🌿 {row['variety']}
                </span>
                <span style="font-size:0.8rem; color:#6B5E4E;">
                    {row['start_date']} → {row['end_date']}
                </span>
            </div>
            <div style="font-size:0.82rem; color:#6B5E4E; margin-top:0.3rem;">
                {row['summary'][:200] + ('…' if len(row['summary']) > 200 else '')}
            </div>
            <div style="font-size:0.75rem; color:#9B8E7E; margin-top:0.2rem;">
                {row['created_at']}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Pestaña 2: Riesgos detectados ────────────────────────────────────────────
def tab_riesgos(result: dict) -> None:
    risks = result.get("risk_explanation", [])
    priority_map = {
        "crítico": ("alerta-critica", "🔴"),
        "alto":    ("alerta-critica", "🟠"),
        "medio":   ("alerta-media",   "🟡"),
        "bajo":    ("alerta-baja",    "🟢"),
    }

    if not risks:
        st.markdown("""
        <div class="alerta-baja" style="margin-top:1rem;">
            🟢 <strong>No se han detectado riesgos significativos</strong>
            en el periodo analizado.
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"**{len(risks)} riesgo(s) detectado(s)** en el periodo de análisis.")
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    for risk in risks:
        level = risk.get("level", "bajo")
        if hasattr(level, "value"):
            level = level.value
        css_class, emoji = priority_map.get(str(level).lower(), ("alerta-baja", "⚪"))

        with st.expander(
            f"{emoji} {risk.get('type','Riesgo').replace('_',' ').capitalize()} — nivel {level}",
            expanded=(str(level).lower() in ("alto","crítico"))
        ):
            col_info, col_detalle = st.columns([1, 2])
            with col_info:
                st.markdown(f"""
                <div class="{css_class}" style="margin:0;">
                    <div style="font-size:0.8rem; color:#4A3728;">
                        <strong>Nivel:</strong> {level}<br>
                        <strong>Valor:</strong> {risk.get('value','—')}<br>
                        <strong>Umbral:</strong> {risk.get('threshold','—')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_detalle:
                desc = risk.get("description","")
                if desc:
                    st.markdown(f"**Descripción:** {desc}")

                causes = risk.get("causes", [])
                if causes:
                    st.markdown("**Causas:**")
                    for c in causes[:3]:
                        cond = f" *({c.get('condition','')})*" if c.get("condition") else ""
                        st.markdown(f"- {c.get('label','—')}{cond}")

                effects = risk.get("effects", [])
                if effects:
                    st.markdown("**Efectos sobre la vid:**")
                    for e in effects[:3]:
                        st.markdown(f"- {e.get('relation','afecta').capitalize()} {e.get('label','—')}")

                actions = risk.get("recommended_actions", [])
                if actions:
                    st.markdown("**Acciones recomendadas:**")
                    for a in actions[:2]:
                        cond = f" *({a.get('condition','')})*" if a.get("condition") else ""
                        st.markdown(f"- ✅ {a.get('label','—')}{cond}")

                phases = risk.get("vulnerable_phases", [])
                if phases:
                    st.markdown("**Fases más vulnerables:** " +
                                ", ".join(p if isinstance(p, str) else p.get("label","") for p in phases))

    # Alternativas al final
    alternatives = result.get("alternatives", [])
    if alternatives:
        st.markdown("<div class='divider-vid'></div>", unsafe_allow_html=True)
        st.markdown("#### 🔀 Escenarios alternativos evaluados")
        alt_cols = st.columns(len(alternatives[:2]))
        for i, alt in enumerate(alternatives[:2]):
            utility   = alt.get("utility")
            util_text = f"{utility:.2f}" if isinstance(utility, (int, float)) else "—"
            with alt_cols[i]:
                with st.container(border=True):
                    st.markdown(f"**Alternativa {i+1}** · Utilidad: `{util_text}`")
                    st.caption(alt.get("tradeoff", ""))
                    for a in alt.get("actions", []):
                        st.markdown(f"- {str(a).replace('_',' ').capitalize()}")


# ── Pestaña 3: Plan diario ────────────────────────────────────────────────────
def tab_plan_diario(result: dict) -> None:
    plan_text = result.get("daily_plan_text", "")
    reasoning = result.get("recommendation_reasoning", "")
    sms_text  = result.get("sms_text", "")

    col_plan, col_sms = st.columns([3, 2])

    with col_plan:
        st.markdown("#### 📅 Plan de actuación recomendado")
        if plan_text:
            st.markdown(f"""
            <div style="background:#F5F0E8; border-radius:12px; padding:1.2rem 1.5rem;
                        line-height:1.9; font-size:0.95rem;">
                {plan_text}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Plan diario no disponible.")

        if reasoning:
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            with st.expander("🧠 Justificación de la recomendación"):
                st.markdown(reasoning)

    with col_sms:
        st.markdown("#### 📱 Resumen SMS")
        if sms_text:
            st.markdown(f"""
            <div class="sms-box">{sms_text.replace(chr(10),'<br>')}</div>
            <div style="font-size:0.75rem; color:#6B5E4E; margin-top:0.4rem; text-align:right;">
                {len(sms_text)}/160 caracteres
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("SMS no disponible.")

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown("#### 🔍 Confianza del análisis")
        confidence = result.get("confidence", {})
        conf_label = confidence.get("label", "N/D")
        conf_score = confidence.get("score", "—")
        conf_color = {"alta": "#3B6B2A", "media": "#C8832A",
                      "baja": "#C0392B"}.get(conf_label, "#6B5E4E")
        st.markdown(f"""
        <div style="background:#F5F0E8; border-radius:10px; padding:1rem;
                    text-align:center; border: 1px solid #E8E2D9;">
            <div style="font-size:2rem; font-family:'Playfair Display',serif;
                        color:{conf_color}; font-weight:700;">{conf_score}</div>
            <div style="font-size:0.85rem; color:{conf_color}; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.05em;">{conf_label}</div>
        </div>
        """, unsafe_allow_html=True)
        reasons = confidence.get("reasons", [])
        if reasons:
            st.caption("Factores: " + ", ".join(reasons))


# ── Pestaña 4: Escuchar resumen ───────────────────────────────────────────────
def tab_audio(result: dict) -> None:
    summary  = result.get("summary", "")
    sms_text = result.get("sms_text", "")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("#### 🔊 Escuchar recomendación")
        st.markdown("""
        <p style="color:#6B5E4E; font-size:0.9rem; margin-bottom:1rem;">
            Genera un audio con el resumen del análisis para escucharlo
            sin necesidad de leer la pantalla.
        </p>
        """, unsafe_allow_html=True)

        texto_audio = st.radio(
            "¿Qué quieres escuchar?",
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

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        if st.button("🎙️ Generar audio", use_container_width=True):
            if not contenido:
                st.warning("No hay texto disponible para generar el audio.")
            else:
                try:
                    from web.voice import generate_voice_file
                    with st.spinner("Generando audio..."):
                        audio_path = generate_voice_file(contenido)
                    if audio_path and Path(audio_path).exists():
                        st.audio(Path(audio_path).read_bytes(), format="audio/mp3")
                        st.success("✓ Audio generado correctamente.")
                    else:
                        st.warning("No se pudo generar el audio.")
                except Exception as e:
                    st.error(f"Error al generar el audio: {e}")

    with col_right:
        st.markdown("#### 📋 Texto completo")
        st.markdown(f"""
        <div style="background:#F5F0E8; border-radius:12px; padding:1.2rem;
                    font-size:0.9rem; line-height:1.8; color:#2C2416;
                    border: 1px solid #E8E2D9; min-height:200px;">
            {summary or 'Sin resumen disponible.'}
        </div>
        """, unsafe_allow_html=True)


# ── Pestaña 5: Configuración del análisis ────────────────────────────────────
def tab_configuracion(user: dict) -> dict:
    st.markdown("#### ⚙️ Configuración del análisis")
    st.markdown("""
    <p style="color:#6B5E4E; font-size:0.9rem; margin-bottom:1.5rem;">
        Modifica los parámetros del análisis y pulsa <strong>Recalcular</strong>
        para obtener nuevas recomendaciones.
    </p>
    """, unsafe_allow_html=True)

    today       = date.today()
    default_end = today + timedelta(days=4)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🌍 Localización y cultivo**")
        station = st.text_input("Código estación AEMET", value=user["station"])
        ccaa    = st.text_input("Comunidad autónoma",    value=user["ccaa"])
        variety = st.text_input("Variedad principal",    value=user["variety"])

    with col2:
        st.markdown("**🌱 Características del viñedo**")
        soil_opts  = ["", "arenoso", "franco", "arcilloso"]
        soil_type  = st.selectbox(
            "Tipo de suelo", options=soil_opts,
            index=soil_opts.index(user.get("soil_type","") or ""),
            format_func=lambda x: "Selecciona..." if x=="" else x.capitalize()
        )
        irr_opts   = ["", "goteo", "aspersión", "secano"]
        irrigation = st.selectbox(
            "Sistema de riego", options=irr_opts,
            index=irr_opts.index(user.get("irrigation_system","") or ""),
            format_func=lambda x: "Selecciona..." if x=="" else x.capitalize()
        )
        obj_opts   = ["equilibrio", "producción", "calidad"]
        objective  = st.selectbox(
            "Objetivo de producción", options=obj_opts,
            index=obj_opts.index(user.get("objective","equilibrio")),
            format_func=str.capitalize
        )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.markdown("**📅 Periodo de análisis**")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Fecha de inicio", value=today)
    with col_d2:
        end_date   = st.date_input("Fecha de fin",    value=default_end)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    col_save, col_recalc, _ = st.columns([1, 1, 2])

    save_prefs = col_save.button("💾 Guardar preferencias", use_container_width=True)
    recalc     = col_recalc.button("🔄 Recalcular análisis", use_container_width=True,
                                   type="primary")

    if save_prefs:
        update_user_preferences(
            user_id=user["id"], station=station, ccaa=ccaa,
            variety=variety, soil_type=soil_type,
            irrigation_system=irrigation, objective=objective,
        )
        st.session_state.user = {
            **user, "station": station, "ccaa": ccaa,
            "variety": variety, "soil_type": soil_type,
            "irrigation_system": irrigation, "objective": objective,
        }
        st.session_state.analysis_result = None
        st.success("✓ Preferencias guardadas. El análisis se recalculará automáticamente.")
        st.rerun()

    st.markdown("<div class='divider-vid'></div>", unsafe_allow_html=True)
    st.markdown("#### 👤 Información de la cuenta")
    st.markdown(f"""
    <div style="background:#F5F0E8; border-radius:10px; padding:1rem 1.2rem;
                border: 1px solid #E8E2D9;">
        <div style="font-size:0.9rem; color:#6B5E4E;">
            <strong>Email:</strong> {user.get('email','—')}<br>
            <strong>Región configurada:</strong> {user.get('ccaa','—')}<br>
            <strong>Variedad:</strong> {user.get('variety','—')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar sesión", use_container_width=False):
        st.session_state.user = None
        st.session_state.analysis_result = None
        st.rerun()

    return {
        "station": station, "ccaa": ccaa, "variety": variety,
        "soil_type": soil_type, "irrigation_system": irrigation,
        "objective": objective, "start_date": start_date,
        "end_date": end_date, "recalc": recalc,
    }


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    init_db()
    init_session()

    if st.session_state.user is None:
        render_auth()
        return

    user = st.session_state.user
    maybe_run_default_analysis(user)

    result = st.session_state.analysis_result

    # Header siempre visible
    if result:
        render_header(result)

    # Pestañas principales
    t1, t2, t3, t4, t5 = st.tabs([
        "🏠 Inicio",
        "⚠️ Riesgos",
        "📅 Plan diario",
        "🔊 Escuchar",
        "⚙️ Configuración",
    ])

    with t1:
        if result:
            tab_principal(result)
        else:
            st.info("Calculando el análisis inicial...")

    with t2:
        if result:
            tab_riesgos(result)
        else:
            st.info("El análisis aún no está disponible.")

    with t3:
        if result:
            tab_plan_diario(result)
        else:
            st.info("El análisis aún no está disponible.")

    with t4:
        if result:
            tab_audio(result)
        else:
            st.info("El análisis aún no está disponible.")

    with t5:
        prefs = tab_configuracion(user)
        if prefs["recalc"]:
            try:
                from web.runner import run_analysis, save_analysis
                with st.spinner("🌿 Recalculando análisis..."):
                    new_result = run_analysis(
                        station=prefs["station"], ccaa=prefs["ccaa"],
                        variety=prefs["variety"],
                        start_date=prefs["start_date"],
                        end_date=prefs["end_date"],
                    )
                    st.session_state.analysis_result = new_result
                    save_analysis(user["id"], new_result)
                    st.success("✓ Análisis actualizado. Ve a la pestaña Inicio para ver los resultados.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error al recalcular: {e}")


if __name__ == "__main__":
    main()