from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from web.auth import login_user, register_user, update_user_preferences
from web.db import init_db

def init_session() -> None:
    if "user" not in st.session_state:
        st.session_state.user = None
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None


def logout() -> None:
    st.session_state.user = None
    st.session_state.analysis_result = None
    st.rerun()


def render_auth() -> None:
    st.title("🍇 Agri Agent")
    st.caption("Recomendaciones agrícolas con análisis agroclimático")

    tab_login, tab_register = st.tabs(["Iniciar sesión", "Crear cuenta"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            user = login_user(email, password)
            if user:
                st.session_state.user = user
                st.success("Sesión iniciada.")
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")

    with tab_register:
        with st.form("register_form"):
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Contraseña", type="password", key="reg_password")
            station = st.text_input("Estación", value="9995Y")
            ccaa = st.text_input("Región / CCAA", value="Navarra")
            variety = st.text_input("Variedad", value="Tempranillo")
            soil_type = st.selectbox(
                "Tipo de suelo",
                ["", "arenoso", "franco", "arcilloso"],
            )
            irrigation_system = st.selectbox(
                "Sistema de riego",
                ["", "goteo", "aspersión", "secano"],
            )
            objective = st.selectbox(
                "Objetivo",
                ["equilibrio", "producción", "calidad"],
            )
            submitted = st.form_submit_button("Crear cuenta", use_container_width=True)

        if submitted:
            ok, msg = register_user(
                email=email,
                password=password,
                station=station,
                ccaa=ccaa,
                variety=variety,
                soil_type=soil_type,
                irrigation_system=irrigation_system,
                objective=objective,
            )
            if ok:
                st.success(msg)
            else:
                st.error(msg)


def render_sidebar(user: dict) -> dict:
    st.sidebar.title("Mi configuración")
    st.sidebar.write(f"**{user['email']}**")

    today = date.today()
    default_end = today + timedelta(days=4)

    with st.sidebar.form("preferences_form"):
        station = st.text_input("Estación", value=user["station"])
        ccaa = st.text_input("Región / CCAA", value=user["ccaa"])
        variety = st.text_input("Variedad", value=user["variety"])

        soil_type = st.selectbox(
            "Tipo de suelo",
            ["", "arenoso", "franco", "arcilloso"],
            index=["", "arenoso", "franco", "arcilloso"].index(user.get("soil_type", "") or ""),
        )

        irrigation_system = st.selectbox(
            "Sistema de riego",
            ["", "goteo", "aspersión", "secano"],
            index=["", "goteo", "aspersión", "secano"].index(user.get("irrigation_system", "") or ""),
        )

        objective = st.selectbox(
            "Objetivo",
            ["equilibrio", "producción", "calidad"],
            index=["equilibrio", "producción", "calidad"].index(user.get("objective", "equilibrio")),
        )

        start_date = st.date_input("Fecha inicio", value=today)
        end_date = st.date_input("Fecha fin", value=default_end)

        c1, c2 = st.columns(2)
        save_prefs = c1.form_submit_button("Guardar")
        recalc = c2.form_submit_button("Recalcular")

    if save_prefs:
        update_user_preferences(
            user_id=user["id"],
            station=station,
            ccaa=ccaa,
            variety=variety,
            soil_type=soil_type,
            irrigation_system=irrigation_system,
            objective=objective,
        )
        st.success("Preferencias guardadas.")
        st.session_state.user = {
            **user,
            "station": station,
            "ccaa": ccaa,
            "variety": variety,
            "soil_type": soil_type,
            "irrigation_system": irrigation_system,
            "objective": objective,
        }

    return {
        "station": station,
        "ccaa": ccaa,
        "variety": variety,
        "soil_type": soil_type,
        "irrigation_system": irrigation_system,
        "objective": objective,
        "start_date": start_date,
        "end_date": end_date,
        "recalc": recalc,
    }


def maybe_run_default_analysis(user: dict) -> None:
    if st.session_state.analysis_result is not None:
        return

    today = date.today()
    end = today + timedelta(days=4)

    try:
        from web.runner import run_analysis, save_analysis
    except Exception as e:
        st.error(f"No se pudo cargar el motor de análisis: {e}")
        return

    with st.spinner("Calculando análisis inicial..."):
        try:
            result = run_analysis(
                station=user["station"],
                ccaa=user["ccaa"],
                variety=user["variety"],
                start_date=today,
                end_date=end,
            )
            st.session_state.analysis_result = result
            save_analysis(user["id"], result)
        except Exception as e:
            st.error(f"Error al calcular el análisis inicial: {e}")

    

def render_result(result: dict) -> None:
    meta = result["meta"]

    st.subheader("Resumen")
    st.write(result.get("summary", "Sin resumen."))

    c1, c2, c3 = st.columns(3)
    c1.metric("Región", meta.get("ccaa", "—"))
    c2.metric("Estación", meta.get("station", "—"))
    c3.metric("Variedad", meta.get("variety", "—"))

    st.subheader("Confianza")
    confidence = result.get("confidence", {})
    st.write(f"Nivel: **{confidence.get('label', 'N/D')}**")
    st.write(f"Score: **{confidence.get('score', 'N/D')}**")

    st.subheader("Riesgos detectados")
    risks = result.get("risk_explanation", [])
    if risks:
        for risk in risks:
            with st.container(border=True):
                st.write(f"**{risk.get('type', 'Riesgo')}**")        # ← type, no type_label
                st.write(f"Nivel: {risk.get('level', 'N/D')}")
                st.write(risk.get("description", ""))                  # ← description, no what_it_means
                if risk.get("message"):
                    st.caption(risk["message"])
    else:
        st.info("No hay riesgos destacados.")

    st.subheader("Plan diario")
    st.write(result.get("daily_plan_text", "Sin plan diario."))

    st.subheader("SMS")
    st.code(result.get("sms_text", ""), language=None)

    st.subheader("Escuchar recomendación")
    if st.button("Generar audio", use_container_width=False):
        try:
            from web.voice import generate_voice_file
            with st.spinner("Generando audio..."):
                audio_path = generate_voice_file(result.get("summary", ""))
        except Exception as e:
            st.error(f"Error al generar el audio: {e}")
            return
        if audio_path and Path(audio_path).exists():
            audio_bytes = Path(audio_path).read_bytes()
            st.audio(audio_bytes, format="audio/mp3")
        else:
            st.warning("No se pudo generar el audio.")


def render_history(user_id: int) -> None:
    st.subheader("Histórico reciente")

    try:
        from web.runner import get_last_analyses
        rows = get_last_analyses(user_id, limit=5)
    except Exception as e:
        st.error(f"No se pudo cargar el histórico: {e}")
        return

    if not rows:
        st.caption("Todavía no hay análisis guardados.")
        return

    for row in rows:
        with st.container(border=True):
            st.write(
                f"**{row['created_at']}** · {row['ccaa']} · {row['variety']} · "
                f"{row['start_date']} → {row['end_date']}"
            )
            st.write(row["summary"][:250] + ("..." if len(row["summary"]) > 250 else ""))

def main() -> None:
    init_db()
    init_session()

    if st.session_state.user is None:
        render_auth()
        return

    user = st.session_state.user

    top1, top2 = st.columns([8, 1])
    top1.title("🍇 Panel del agricultor")
    if top2.button("Salir"):
        logout()

    prefs = render_sidebar(user)
    maybe_run_default_analysis(user)

    if prefs["recalc"]:
        try:
            from web.runner import run_analysis, save_analysis
            with st.spinner("Recalculando..."):
                result = run_analysis(
                    station=prefs["station"],
                    ccaa=prefs["ccaa"],
                    variety=prefs["variety"],
                    start_date=prefs["start_date"],
                    end_date=prefs["end_date"],
                )
                st.session_state.analysis_result = result
                save_analysis(user["id"], result)
        except Exception as e:
            st.error(f"Error al recalcular: {e}")

    result = st.session_state.analysis_result
    if result:
        render_result(result)
        st.divider()
        render_history(user["id"])


if __name__ == "__main__":
    main()