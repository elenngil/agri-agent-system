from models.shared_state import SharedState, Alert, RiskLevel


class RiskAgent:
    """Convierte riesgos y predicciones en alertas accionables."""

    def __init__(self, penalties: dict | None = None):
        self.penalties = penalties or {
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.8,
            RiskLevel.CRITICAL: 1.0,
        }

    def run(self, state: SharedState) -> SharedState:
        alerts = []

        if state.climate_features is None:
            raise ValueError("climate_features no está disponible en shared_state")
        if state.predictions is None:
            raise ValueError("predictions no está disponible en shared_state")

        climate = state.climate_features
        predictions = state.predictions

        for risk_type, risk_data, template in [
            (
                "frost_risk",
                climate.frost_risk,
                "Riesgo de helada {level}: temperatura mínima observada {value}°C frente al umbral del cultivo {threshold}°C.",
            ),
            (
                "heat_stress",
                climate.heat_stress,
                "Estrés térmico {level}: temperatura máxima observada {value}°C frente al umbral del cultivo {threshold}°C.",
            ),
            (
                "mildiu_risk",
                climate.mildiu_risk,
                "Riesgo de mildiu {level}: humedad observada {value} frente al umbral {threshold}.",
            ),
            (
                "strong_wind_risk",
                climate.strong_wind_risk,
                "Riesgo de viento fuerte {level}: velocidad observada {value} frente al umbral {threshold}.",
            ),
        ]:
            alert = self._build_alert_from_risk_dict(
                risk_type=risk_type,
                risk_data=risk_data,
                ccaa=state.ccaa,
                valid_until=str(state.end_date),
                message_template=template,
            )
            if alert:
                alerts.append(alert)

        water_alert = self._build_alert_from_prediction(
            risk_type="future_water_stress",
            level=predictions.future_water_stress,
            ccaa=state.ccaa,
            valid_until=str(state.end_date),
            message_template="Estrés hídrico futuro {level} para el periodo analizado.",
        )
        if water_alert:
            alerts.append(water_alert)

        irrigation_alert = self._build_alert_from_prediction(
            risk_type="irrigation_need",
            level=predictions.irrigation_need,
            ccaa=state.ccaa,
            valid_until=str(state.end_date),
            message_template="Necesidad de riego {level} para el periodo analizado.",
        )
        if irrigation_alert:
            alerts.append(irrigation_alert)

        alerts.sort(key=lambda a: a.penalty, reverse=True)
        state.alerts = alerts
        return state

    def _normalize_level(self, level: str | RiskLevel | None) -> RiskLevel | None:
        if level is None:
            return None

        if isinstance(level, RiskLevel):
            return level

        text = str(level).strip().lower()

        mapping = {
            "bajo": RiskLevel.LOW,
            "baja": RiskLevel.LOW,
            "medio": RiskLevel.MEDIUM,
            "media": RiskLevel.MEDIUM,
            "moderado": RiskLevel.MEDIUM,
            "moderada": RiskLevel.MEDIUM,
            "alto": RiskLevel.HIGH,
            "alta": RiskLevel.HIGH,
            "crítico": RiskLevel.CRITICAL,
            "critico": RiskLevel.CRITICAL,
        }

        return mapping.get(text)

    def _build_alert_from_risk_dict(
        self,
        risk_type: str,
        risk_data: dict | str | None,
        ccaa: str,
        valid_until: str,
        message_template: str,
    ) -> Alert | None:
        if risk_data is None:
            return None

        if isinstance(risk_data, dict):
            raw_level = risk_data.get("level")
            value = risk_data.get("value")
            threshold = risk_data.get("threshold")
        else:
            raw_level = risk_data
            value = None
            threshold = None

        level = self._normalize_level(raw_level)

        if level is None or level == RiskLevel.LOW:
            return None

        penalty = self.penalties.get(level, 0.0)

        return Alert(
            risk_type=risk_type,
            level=level,
            value=value,
            threshold=threshold,
            penalty=penalty,
            ccaa=ccaa,
            valid_until=valid_until,
            message=message_template.format(
                level=level.value,
                value=value,
                threshold=threshold,
            ),
        )

    def _build_alert_from_prediction(
        self,
        risk_type: str,
        level: str | RiskLevel | None,
        ccaa: str,
        valid_until: str,
        message_template: str,
    ) -> Alert | None:
        normalized_level = self._normalize_level(level)

        if normalized_level is None or normalized_level == RiskLevel.LOW:
            return None

        penalty = self.penalties.get(normalized_level, 0.0)

        return Alert(
            risk_type=risk_type,
            level=normalized_level,
            value=normalized_level.value,
            threshold=None,
            penalty=penalty,
            ccaa=ccaa,
            valid_until=valid_until,
            message=message_template.format(level=normalized_level.value),
        )