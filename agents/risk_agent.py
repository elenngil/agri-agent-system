from models.shared_state import SharedState, Alert


class RiskAgent:
    """Convierte riesgos y predicciones en alertas accionables."""

    def __init__(self, penalties: dict | None = None):
        self.penalties = penalties or {
            "Bajo": 0.2,
            "Moderado": 0.5,
            "Alto": 0.8,
            "Nulo": 0.0,
            "Desconocido": 0.0,
            "Baja": 0.2,
            "Media": 0.5,
            "Alta": 0.8,
        }

    def run(self, state: SharedState) -> SharedState:
        alerts = []

        if state.climate_features is None:
            raise ValueError("climate_features no está disponible en shared_state")
        if state.predictions is None:
            raise ValueError("predictions no está disponible en shared_state")

        climate = state.climate_features
        predictions = state.predictions

        # Riesgo de helada
        frost_alert = self._build_alert_from_risk_dict(
            risk_type="frost_risk",
            risk_data=climate.frost_risk,
            ccaa=state.ccaa,
            valid_until=str(state.end_date),
            message_template="Riesgo de helada {level}: temperatura mínima observada {value}°C frente al umbral del cultivo {threshold}°C."
        )
        if frost_alert:
            alerts.append(frost_alert)

        # Estrés térmico
        heat_alert = self._build_alert_from_risk_dict(
            risk_type="heat_stress",
            risk_data=climate.heat_stress,
            ccaa=state.ccaa,
            valid_until=str(state.end_date),
            message_template="Estrés térmico {level}: temperatura máxima observada {value}°C frente al umbral del cultivo {threshold}°C."
        )
        if heat_alert:
            alerts.append(heat_alert)

        # Mildiu
        mildiu_alert = self._build_alert_from_risk_dict(
            risk_type="mildiu_risk",
            risk_data=climate.mildiu_risk,
            ccaa=state.ccaa,
            valid_until=str(state.end_date),
            message_template="Riesgo de mildiu {level}: humedad observada {value} frente al umbral {threshold}."
        )
        if mildiu_alert:
            alerts.append(mildiu_alert)

        # Viento fuerte
        wind_alert = self._build_alert_from_risk_dict(
            risk_type="strong_wind_risk",
            risk_data=climate.strong_wind_risk,
            ccaa=state.ccaa,
            valid_until=str(state.end_date),
            message_template="Riesgo de viento fuerte {level}: velocidad observada {value} frente al umbral {threshold}."
        )
        if wind_alert:
            alerts.append(wind_alert)

        # Estrés hídrico futuro
        water_alert = self._build_alert_from_prediction(
            risk_type="future_water_stress",
            level=predictions.future_water_stress,
            ccaa=state.ccaa,
            valid_until=str(state.end_date),
            message_template="Estrés hídrico futuro {level} para el periodo analizado."
        )
        if water_alert:
            alerts.append(water_alert)

        # Necesidad de riego
        irrigation_alert = self._build_alert_from_prediction(
            risk_type="irrigation_need",
            level=predictions.irrigation_need,
            ccaa=state.ccaa,
            valid_until=str(state.end_date),
            message_template="Necesidad de riego {level} para el periodo analizado."
        )
        if irrigation_alert:
            alerts.append(irrigation_alert)

        alerts.sort(key=lambda a: a.penalty, reverse=True)
        state.alerts = alerts
        return state

    def _build_alert_from_risk_dict(
        self,
        risk_type: str,
        risk_data: dict | None,
        ccaa: str,
        valid_until: str,
        message_template: str
    ) -> Alert | None:
        if risk_data is None:
            return None

        level = risk_data.get("level")
        if level in ("Bajo", "Nulo", "Desconocido", None):
            return None

        penalty = self.penalties.get(level, 0.0)

        return Alert(
            risk_type=risk_type,
            level=level.lower(),
            value=risk_data.get("value"),
            threshold=risk_data.get("threshold"),
            penalty=penalty,
            ccaa=ccaa,
            valid_until=valid_until,
            message=message_template.format(
                level=level.lower(),
                value=risk_data.get("value"),
                threshold=risk_data.get("threshold")
            )
        )

    def _build_alert_from_prediction(
        self,
        risk_type: str,
        level: str | None,
        ccaa: str,
        valid_until: str,
        message_template: str
    ) -> Alert | None:
        if level in (None, "Bajo", "Baja", "Desconocido"):
            return None

        penalty = self.penalties.get(level, 0.0)

        return Alert(
            risk_type=risk_type,
            level=level.lower(),
            value=level,
            threshold=None,
            penalty=penalty,
            ccaa=ccaa,
            valid_until=valid_until,
            message=message_template.format(level=level.lower())
        )