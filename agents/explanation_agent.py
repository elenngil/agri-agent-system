from models.shared_state import SharedState
from rag.retriever import get_retriever


class ExplanationAgent:
    """Genera explicaciones en lenguaje natural para riesgos y escenarios recomendados."""

    def __init__(self, model):
        self.model = model

    def run(self, state: SharedState) -> SharedState:
        if not state.scenarios:
            raise ValueError("scenarios no está disponible en shared_state")

        best_scenario = state.scenarios[0]
        alerts = state.alerts
        climate = state.climate_features
        predictions = state.predictions
        crop = state.crop_data

        confidence = self._estimate_confidence(state, best_scenario)

        explanation = {
            "summary": self._generate_summary(state, best_scenario, confidence),
            "confidence": confidence,
            "decision_why": self._explain_decision_why(state, best_scenario, confidence),
            "risk_explanation": self._explain_risks(alerts[:3]),
            "recommendation_reasoning": self._explain_recommendation(best_scenario, climate, predictions, crop),
            "alternatives": self._explain_alternatives(state.scenarios[1:]),
            "sms_text": self._generate_sms(best_scenario, alerts[:2], state.ccaa, state),
        }

        state.explanation = explanation
        return state

    def _generate_summary(self, state: SharedState, best_scenario, confidence: dict) -> str:
        alerts_text = "\n".join(
            [
                f"- {self._pretty_risk_name(a.risk_type)}: nivel {a.level}, valor observado {a.value}, umbral {a.threshold}"
                for a in state.alerts
            ]
        ) or "- Sin alertas relevantes"

        actions_text = "\n".join(
            [
                f"- {self._humanize_action(a)} (coste {a.cost:.2f})"
                for a in best_scenario.actions
                if a.intensity not in ("none", "normal")
            ]
        ) or "- Mantener manejo actual"

        rag_context = self._enrich_with_rag(state)
        rag_block = f"\nDocumentación técnica de referencia:\n{rag_context}\n" if rag_context else ""
        prompt = f"""
        Eres un asistente agrícola que explica recomendaciones a un viticultor.
        Contexto:
        - Región: {state.ccaa}
        - Estación: {state.station}
        - Periodo analizado: {state.start_date} a {state.end_date}
        - Variedad: {state.crop_data.variety if state.crop_data else "desconocida"}
        Datos relevantes:
        - Temperatura mínima: {state.weather_data.temperature_min if state.weather_data else "N/D"} °C
        - Temperatura máxima: {state.weather_data.temperature_max if state.weather_data else "N/D"} °C
        - Precipitación acumulada: {state.weather_data.precipitation if state.weather_data else "N/D"} mm
        - ETc: {state.climate_features.etc if state.climate_features else "N/D"}
        - DHA: {state.climate_features.dha if state.climate_features else "N/D"}
        Riesgos detectados:
        {alerts_text}
        Predicciones:
        - Estrés hídrico futuro: {state.predictions.future_water_stress if state.predictions else "N/D"}
        - Necesidad de riego: {state.predictions.irrigation_need if state.predictions else "N/D"}
        Mejor escenario:
        - Utilidad: {best_scenario.utility:.2f}
        - Confianza estimada: {confidence["score"]:.2f}
        Acciones recomendadas:
        {actions_text}
        {rag_block}
        Escribe una explicación en español con ESTE FORMATO EXACTO:
        Resumen:
        <2 o 3 frases claras y prácticas>
        Motivo principal:
        <1 o 2 frases explicando por qué se eligió esta recomendación>
        Confianza:
        <1 frase breve explicando el nivel de confianza>
        Reglas:
        - Usa lenguaje natural
        - No uses nombres técnicos como frost_risk o irrigation_need
        - Usa saltos de línea entre bloques
        - Sé claro, directo y útil para un viticultor
        - Si hay documentación técnica de referencia, úsala para fundamentar las recomendaciones
        """

        try:
            response = self.model.generate(
                messages=[{"role": "user", "content": prompt}]
            )
            text = response if isinstance(response, str) else str(response)
            return text.strip()
        except Exception:
            return self._generate_summary_fallback(state, best_scenario, confidence)

    def _generate_summary_fallback(self, state: SharedState, best_scenario, confidence: dict) -> str:
        main_alert = state.alerts[0] if state.alerts else None
        main_action = self._get_main_action(best_scenario)

        if main_alert:
            return (
                f"Resumen:\n"
                f"En {state.ccaa} se detecta como riesgo principal {self._pretty_risk_name(main_alert.risk_type)} "
                f"con nivel {main_alert.level}. La recomendación principal es {main_action}.\n\n"
                f"Motivo principal:\n"
                f"Se ha elegido este escenario porque ofrece el mejor equilibrio entre calidad, producción, "
                f"coste y sostenibilidad dentro de las alternativas analizadas.\n\n"
                f"Confianza:\n"
                f"El nivel de confianza estimado es {confidence['label']} ({confidence['score']:.2f}) "
                f"porque la recomendación se apoya en datos climáticos observados y reglas explícitas del sistema."
            )

        return (
            f"Resumen:\n"
            f"En {state.ccaa} no se han detectado alertas relevantes en el periodo analizado.\n\n"
            f"Motivo principal:\n"
            f"Se recomienda mantener el manejo actual porque no aparecen riesgos que justifiquen una intervención.\n\n"
            f"Confianza:\n"
            f"El nivel de confianza estimado es {confidence['label']} ({confidence['score']:.2f})."
        )

    def _estimate_confidence(self, state: SharedState, best_scenario) -> dict:
        score = 0.5
        reasons = []

        if state.weather_data is not None:
            score += 0.15
            reasons.append("hay datos meteorológicos disponibles")

            if getattr(state.weather_data, "days_count", 0) >= 3:
                score += 0.10
                reasons.append("el análisis cubre varios días")

        if state.crop_data is not None:
            score += 0.10
            reasons.append("hay información del cultivo")

        if state.climate_features is not None:
            score += 0.10
            reasons.append("se han calculado variables agroclimáticas")

        if state.predictions is not None:
            score += 0.05
            reasons.append("hay predicciones derivadas")

        if state.alerts:
            score += 0.05
            reasons.append("los riesgos están priorizados")

        if best_scenario.utility >= 0.75:
            score += 0.05
            reasons.append("el escenario recomendado tiene alta utilidad")

        if len(state.scenarios) >= 3:
            score += 0.05
            reasons.append("se compararon varias alternativas")

        score = max(0.0, min(1.0, score))

        if score >= 0.8:
            label = "alta"
        elif score >= 0.6:
            label = "media"
        else:
            label = "baja"

        return {
            "score": round(score, 2),
            "label": label,
            "reasons": reasons,
        }

    def _explain_decision_why(self, state: SharedState, best_scenario, confidence: dict) -> dict:
        main_action = self._get_main_action(best_scenario)
        main_alert = state.alerts[0] if state.alerts else None

        if main_alert:
            short_reason = (
                f"La decisión se toma principalmente por {self._pretty_risk_name(main_alert.risk_type)} "
                f"de nivel {main_alert.level}, y porque la acción recomendada '{main_action}' "
                f"maximiza la utilidad total del escenario."
            )
        else:
            short_reason = (
                f"La decisión se toma porque no se detectan riesgos relevantes y el escenario "
                f"seleccionado mantiene el mejor equilibrio global."
            )

        return {
            "main_action": main_action,
            "main_alert": self._pretty_risk_name(main_alert.risk_type) if main_alert else None,
            "utility": best_scenario.utility,
            "confidence_score": confidence["score"],
            "short_reason": short_reason,
            "breakdown_interpretation": self._interpret_breakdown(best_scenario.breakdown),
        }

    def _interpret_breakdown(self, breakdown: dict) -> dict:
        return {
            "quality": f"Impacto estimado en calidad: {breakdown.get('quality', 0):.2f}",
            "production": f"Impacto estimado en producción: {breakdown.get('production', 0):.2f}",
            "cost": f"Evaluación del coste: {breakdown.get('cost', 0):.2f}",
            "sustainability": f"Evaluación de sostenibilidad: {breakdown.get('sustainability', 0):.2f}",
        }

    def _explain_risks(self, alerts) -> list[dict]:
        explanations = []

        for alert in alerts:
            explanations.append({
                "type": alert.risk_type,
                "type_label": self._pretty_risk_name(alert.risk_type),
                "level": alert.level,
                "value": alert.value,
                "threshold": alert.threshold,
                "what_it_means": self._risk_description(alert.risk_type),
                "valid_until": alert.valid_until,
                "message": alert.message,
            })

        return explanations

    def _risk_description(self, risk_type: str) -> str:
        descriptions = {
            "frost_risk": "Existe posibilidad de heladas que pueden dañar brotes, hojas jóvenes o frenar el desarrollo del cultivo.",
            "mildiu_risk": "Se observan condiciones favorables para el desarrollo de mildiu por humedad elevada.",
            "heat_stress": "Las temperaturas pueden afectar negativamente a la planta y a la maduración.",
            "future_water_stress": "Se prevé un posible déficit hídrico en el periodo analizado.",
            "irrigation_need": "Se estima necesidad de aportar riego para mantener condiciones adecuadas.",
            "strong_wind_risk": "El viento puede generar daños físicos o aumentar el estrés de la planta.",
        }
        return descriptions.get(risk_type, "Se ha detectado un riesgo agroclimático relevante.")

    def _explain_recommendation(self, best_scenario, climate, predictions, crop) -> dict:
        return {
            "selected_actions": [
                {
                    "type": action.type,
                    "type_label": self._pretty_action_type(action.type),
                    "intensity": action.intensity,
                    "intensity_label": self._pretty_intensity(action.intensity),
                    "cost": action.cost,
                }
                for action in best_scenario.actions
            ],
            "utility": best_scenario.utility,
            "breakdown": best_scenario.breakdown,
            "why": self._recommendation_text(best_scenario),
        }

    def _recommendation_text(self, best_scenario) -> str:
        main_action = self._get_main_action(best_scenario)
        return (
            f"Este escenario se recomienda porque la acción principal es {main_action} "
            f"y consigue el mejor equilibrio entre utilidad, coste y sostenibilidad."
        )

    def _explain_alternatives(self, scenarios) -> list[dict]:
        alternatives = []

        for scenario in scenarios[:2]:
            alternatives.append({
                "utility": scenario.utility,
                "actions": [
                    {
                        "type": action.type,
                        "type_label": self._pretty_action_type(action.type),
                        "intensity": action.intensity,
                        "intensity_label": self._pretty_intensity(action.intensity),
                        "cost": action.cost,
                    }
                    for action in scenario.actions
                ],
                "breakdown": scenario.breakdown,
                "summary": self._alternative_summary(scenario),
            })

        return alternatives

    def _alternative_summary(self, scenario) -> str:
        actions_text = ", ".join(
            [self._humanize_action(a) for a in scenario.actions if a.intensity not in ("none", "normal")]
        )

        if not actions_text:
            actions_text = "sin medidas adicionales"

        return f"Escenario alternativo con utilidad {scenario.utility:.2f}, basado en {actions_text}."

    def _generate_sms(self, best_scenario, top_alerts, ccaa, state=None) -> str:
        # Periodo
        period = ""
        if state and state.start_date and state.end_date:
            period = f" · {state.start_date} a {state.end_date}"

        # Alertas
        if top_alerts:
            alert = top_alerts[0]  # Solo la principal para no saturar
            level_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(alert.level, "⚠️")
            risk_text = f"{level_emoji} {self._pretty_risk_name(alert.risk_type)} (nivel {alert.level})"
        else:
            risk_text = "🟢 Condiciones estables"

        # Acción principal
        main_action = self._get_main_action(best_scenario)
        action_text = main_action.capitalize()

        # Coste aproximado
        total_cost = sum(a.cost for a in best_scenario.actions)
        if total_cost < 50:
            cost_label = "bajo"
        elif total_cost < 150:
            cost_label = "medio"
        else:
            cost_label = "alto"

        sms = f"🍇 {ccaa}{period}\n{risk_text}\n✅ {action_text}\n💰 Coste estimado: {cost_label}"
        return sms[:160]


    def _risk_emoji(self, risk_type: str) -> str:
        emojis = {
            "frost_risk": "🥶",
            "heat_stress": "🌡️",
            "mildiu_risk": "🍄",
            "future_water_stress": "💧",
            "irrigation_need": "🚿",
            "strong_wind_risk": "💨",
        }
        return emojis.get(risk_type, "⚠️")

    def _get_main_action(self, scenario) -> str:
        priority_order = ["harvest_timing", "irrigation", "fungicide", "canopy_management"]

        for action_type in priority_order:
            action = next((a for a in scenario.actions if a.type == action_type), None)
            if action and action.intensity not in ("none", "normal"):
                return self._humanize_action(action)

        return "mantener manejo actual"

    def _humanize_action(self, action) -> str:
        mapping = {
            ("irrigation", "light"): "aplicar riego ligero",
            ("irrigation", "moderate"): "aplicar riego moderado",
            ("irrigation", "intensive"): "aplicar riego intensivo",
            ("fungicide", "preventive"): "aplicar tratamiento preventivo",
            ("fungicide", "curative"): "aplicar tratamiento curativo",
            ("harvest_timing", "early"): "adelantar la cosecha",
            ("harvest_timing", "delayed"): "retrasar la cosecha",
            ("canopy_management", "light_defoliation"): "realizar defoliación ligera",
            ("canopy_management", "heavy_defoliation"): "realizar defoliación intensa",
        }
        return mapping.get((action.type, action.intensity), f"{action.type}: {action.intensity}")

    def _pretty_risk_name(self, risk_type: str) -> str:
        mapping = {
            "frost_risk": "riesgo de helada",
            "heat_stress": "estrés térmico",
            "mildiu_risk": "riesgo de mildiu",
            "future_water_stress": "estrés hídrico futuro",
            "irrigation_need": "necesidad de riego",
            "strong_wind_risk": "riesgo de viento fuerte",
        }
        return mapping.get(risk_type, risk_type)

    def _pretty_action_type(self, action_type: str) -> str:
        mapping = {
            "irrigation": "riego",
            "fungicide": "tratamiento fungicida",
            "harvest_timing": "momento de cosecha",
            "canopy_management": "manejo de canopy",
        }
        return mapping.get(action_type, action_type)

    def _pretty_intensity(self, intensity: str) -> str:
        mapping = {
            "none": "sin acción",
            "light": "ligero",
            "moderate": "moderado",
            "intensive": "intensivo",
            "preventive": "preventivo",
            "curative": "curativo",
            "normal": "normal",
            "early": "temprano",
            "delayed": "retrasado",
            "light_defoliation": "defoliación ligera",
            "heavy_defoliation": "defoliación intensa",
        }
        return mapping.get(intensity, intensity)
    
    def _enrich_with_rag(self, state: SharedState) -> str:
        """
        Consulta la base vectorial para obtener contexto agronómico
        relevante para los riesgos detectados y la variedad del cultivo.
        Devuelve un string con el contexto, o vacío si no hay nada útil.
        """
        if not state.alerts:
            return ""
        retriever = get_retriever()
        variety   = getattr(state.crop_data, "variety", "vid") if state.crop_data else "vid"
        # Construir query a partir de las alertas reales
        top_risks = [a.risk_type for a in state.alerts[:2]]
        query = f"manejo de {', '.join(top_risks)} en {variety}"
        # Filtros por cultivo (fases las dejamos abiertas para no limitar demasiado)
        chunks = retriever.retrieve(query, top_k=3, filters={"crop": "vid"})
        if not chunks:
            return ""
        return retriever.format_context(chunks)