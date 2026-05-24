from models.shared_state import SharedState, Alert, RiskLevel

class RiskAgent:

    def __init__(self, penalties: dict | None = None):
        self.penalties = penalties or {
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.8,
            RiskLevel.CRITICAL: 1.0,
        }

    def run(self, state: SharedState) -> SharedState:

        if state.climate_features is None:
            raise ValueError("Indicadores no disponibles en SharedState")
        if state.predictions is None:
            raise ValueError("Predicciones no disponibles en SharedState")
        
        alerts = []

        for risk_type, risk_data, template in [
            (
                "frost_risk",
                state.climate_features.frost_risk,
                "Riesgo de helada {level}: temperatura minima observada {value}°C frente al umbral {threshold}°C.",
            ),
            (
                "heat_stress",
                state.climate_features.heat_stress,
                "Estres termico {level}: temperatura maxima observada {value}°C frente al umbral {threshold}°C.",
            ),
            (
                "mildiu_risk",
                state.climate_features.mildiu_risk,
                "Riesgo de mildiu {level}: humedad observada {value}% frente al umbral {threshold}%.",
            ),
            (
                "strong_wind_risk",
                state.climate_features.strong_wind_risk,
                "Riesgo de viento fuerte {level}: velocidad observada {value} km/h frente al umbral {threshold} km/h.",
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


        for risk_type, level, template in [
            (
                "future_water_stress",
                state.predictions.future_water_stress,
                "Estres hidrico futuro {level} para el periodo analizado.",
            ),
            (
                "irrigation_need",
                state.predictions.irrigation_need,
                "Necesidad de riego {level} para el periodo analizado.",
            ),
        ]:
            alert = self._build_alert_from_prediction(
                risk_type=risk_type,
                level=level,
                ccaa=state.ccaa,
                valid_until=str(state.end_date),
                message_template=template,
            )
            if alert:
                alerts.append(alert)


        alerts.sort(key=lambda a: a.penalty, reverse=True)
        state.alerts = alerts
        return state

    def _normalize_level(self, level: str | RiskLevel | None) -> RiskLevel | None:

        if level is None:
            return None
        if isinstance(level, RiskLevel):
            return level

        mapping = {
            "nulo": RiskLevel.LOW,
            "bajo": RiskLevel.LOW,
            "baja": RiskLevel.LOW,
            "medio": RiskLevel.MEDIUM,
            "media": RiskLevel.MEDIUM,
            "moderado": RiskLevel.MEDIUM,
            "moderada": RiskLevel.MEDIUM,
            "alto": RiskLevel.HIGH,
            "alta": RiskLevel.HIGH,
            "critico": RiskLevel.CRITICAL,
            "crítico": RiskLevel.CRITICAL,
            "desconocido": None,
        }
        return mapping.get(str(level).strip().lower())

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
            value     = None
            threshold = None

        level = self._normalize_level(raw_level)
        if level is None or level == RiskLevel.LOW:
            return None

        return Alert(
            risk_type=risk_type,
            level=level,
            value=value,
            threshold=threshold,
            penalty=self.penalties.get(level, 0.0),
            ccaa=ccaa,
            valid_until=valid_until,
            message=message_template.format(
                level=level.value, value=value, threshold=threshold
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

        normalized = self._normalize_level(level)
        if normalized is None or normalized == RiskLevel.LOW:
            return None

        return Alert(
            risk_type=risk_type,
            level=normalized,
            value=normalized.value,
            threshold=None,
            penalty=self.penalties.get(normalized, 0.0),
            ccaa=ccaa,
            valid_until=valid_until,
            message=message_template.format(level=normalized.value),
        )