from datetime import date
import os
from models.shared_state import (
    SharedState,
    DailyPlan,
    IrrigationPlan,
    ClimateSummary,
    CropStatus,
    PreventionItem
)


THRESHOLDS = {
    "heat_stress_temp":   32.0,   
    "cold_stress_temp":   10.0,   
    "frost_risk_temp":     2.0,   
    "rain_threshold":     10.0,   
    "humidity_high":      80.0,   
    "humidity_low":       30.0,   
    "base_irrigation":    6.0,    
    "heat_bonus":         3.0,    
    "cold_reduction":     2.0,    
    "rain_reduction":     4.0,    
}

CROP_PHASES = {
    1:  ("reposo",      "Evitar intervenciones. Proteger ante heladas."),
    2:  ("reposo",      "Preparar suelo y material vegetal para la campaña."),
    3:  ("brotación",   "Vigilar heladas tardías. No intervenir en suelo mojado."),
    4:  ("brotación",   "Inicio activo de crecimiento. Monitorizar plagas tempranas."),
    5:  ("crecimiento", "Aplicar tratamientos preventivos si hay humedad alta."),
    6:  ("crecimiento", "Riego ajustado al calor. Controlar canopy para ventilación."),
    7:  ("maduración",  "Reducir aporte nitrogenado. Mantener riego equilibrado."),
    8:  ("maduración",  "Periodo crítico de calidad. Evitar estrés hídrico severo."),
    9:  ("maduración",  "Vendimia próxima. Monitorizar índices de madurez."),
    10: ("reposo",      "Post-vendimia. Favorecer reservas para el invierno."),
    11: ("reposo",      "Aplicar abonado de fondo si procede."),
    12: ("reposo",      "Poda de invierno cuando la planta esté en dormancia."),
}


class DailyPlanAgent:

    def run(self, state: SharedState) -> SharedState:
        weather  = self._extract_weather(state)
        climate  = self._build_climate_summary(weather)
        irr      = self._build_irrigation_plan(weather, state)
        crop     = self._build_crop_status(state)
        prev     = self._build_prevention(weather, state)
        expl     = self._build_explanation(irr, climate, crop, prev, state)
        sms      = self._build_sms(irr, climate, prev, state)

        state.daily_plan = DailyPlan(
            irrigation=irr,
            climate=climate,
            crop_status=crop,
            prevention=prev,
            explanation=expl,
            sms=sms,
        )
        return state

    def _extract_weather(self, state: SharedState) -> dict:
        w = state.weather_data
        assumed_list = []

        def get(attr, default, label):
            val = getattr(w, attr, None) if w else None
            if val is None:
                assumed_list.append(label)
                return default
            return val

        temp_min  = get("temperature_min", 12.0, "temperatura mínima (asumida 12 °C)")
        temp_max  = get("temperature_max", 24.0, "temperatura máxima (asumida 24 °C)")
        precip    = get("precipitation",    0.0, "precipitación (asumida 0 mm)")
        humidity  = get("humidity",        55.0, "humedad (asumida 55 %)")

        soil_mult = state.soil_multiplier or 1.0

        etc = None
        dha = None
        if state.climate_features:
            etc = getattr(state.climate_features, "etc", None)
            dha = getattr(state.climate_features, "dha", None)

        return {
            "temp_min":      temp_min,
            "temp_max":      temp_max,
            "precipitation": precip,
            "humidity":      humidity,
            "soil_mult":     soil_mult,
            "etc":           etc,
            "dha":           dha,
            "assumed":       assumed_list,
        }


    def _build_climate_summary(self, w: dict) -> ClimateSummary:
        t  = THRESHOLDS
        tmax, tmin, hum = w["temp_max"], w["temp_min"], w["humidity"]

        if tmax >= t["heat_stress_temp"]:
            condition = "estrés térmico"
            interp    = (f"Temperatura máxima de {tmax} °C supera el umbral de {t['heat_stress_temp']} °C. "
                         "Riesgo de quemadura en racimos y aceleración de maduración.")
        elif tmin <= t["frost_risk_temp"]:
            condition = "riesgo de helada"
            interp    = (f"Temperatura mínima de {tmin} °C está en zona de riesgo de helada "
                         f"(umbral {t['frost_risk_temp']} °C). Proteger brotes activos.")
        elif tmax <= t["cold_stress_temp"]:
            condition = "frío"
            interp    = (f"Temperatura máxima de {tmax} °C es baja. "
                         "Desarrollo vegetativo lento, riesgo de enfermedades fúngicas.")
        elif hum >= t["humidity_high"]:
            condition = "húmedo"
            interp    = (f"Humedad relativa del {hum} % favorece el desarrollo de mildiu y botrytis. "
                         "Revisar cobertura fungicida.")
        else:
            condition = "óptimo"
            interp    = (f"Condiciones térmicas ({tmin}–{tmax} °C) y de humedad ({hum} %) "
                         "dentro de rangos favorables para el viñedo.")

        return ClimateSummary(
            condition=condition,
            temp_min=tmin,
            temp_max=tmax,
            precipitation=w["precipitation"],
            humidity=hum,
            interpretation=interp,
        )


    def _build_irrigation_plan(self, w: dict, state: SharedState) -> IrrigationPlan:
        t       = THRESHOLDS
        base    = t["base_irrigation"]
        reasons = []
        assumed = list(w["assumed"])

        adjusted = base

        if w["etc"] is not None:
            adjusted = w["etc"]
            reasons.append(f"base ajustada por ETc ({w['etc']:.1f} L/m²)")
        else:
            reasons.append(f"base estándar de {base} L/m²")

        if w["temp_max"] >= t["heat_stress_temp"]:
            adjusted += t["heat_bonus"]
            reasons.append(f"+{t['heat_bonus']} L/m² por calor extremo (>{t['heat_stress_temp']} °C)")

        elif w["temp_max"] <= t["cold_stress_temp"]:
            adjusted -= t["cold_reduction"]
            reasons.append(f"-{t['cold_reduction']} L/m² por temperatura baja (<{t['cold_stress_temp']} °C)")

        if w["precipitation"] >= t["rain_threshold"]:
            adjusted -= t["rain_reduction"]
            reasons.append(f"-{t['rain_reduction']} L/m² por precipitación ({w['precipitation']:.1f} mm)")

        soil_mult = w["soil_mult"]
        if soil_mult != 1.0:
            adjusted *= soil_mult
            reasons.append(f"×{soil_mult:.2f} por tipo de suelo")

        adjusted = max(0.0, round(adjusted, 1))

        return IrrigationPlan(
            base_liters=base,
            adjusted_liters=adjusted,
            adjustment_reason="; ".join(reasons),
            soil_multiplier=soil_mult,
            assumed_values=assumed,
        )

    def _build_crop_status(self, state: SharedState) -> CropStatus:
        month = None
        assumed = False

        if state.start_date:
            try:
                if hasattr(state.start_date, "month"):
                    month = state.start_date.month
                else:
                    month = int(str(state.start_date)[5:7])
            except (ValueError, IndexError):
                pass

        if month is None:
            month = date.today().month
            assumed = True

        phase, recommendation = CROP_PHASES.get(month, ("desconocida", "Sin datos de fase disponibles."))

        if state.crop_data:
            variety = getattr(state.crop_data, "variety", None)
            if variety:
                recommendation = f"[{variety}] {recommendation}"

        return CropStatus(
            phase=phase,
            recommendation=recommendation,
            assumed=assumed,
        )


    def _build_prevention(self, w: dict, state: SharedState) -> list[PreventionItem]:
        items = []
        t = THRESHOLDS

        if w["temp_min"] <= t["frost_risk_temp"] + 3:
            items.append(PreventionItem(
                risk="frost_risk",
                label="Riesgo de helada",
                priority="alta" if w["temp_min"] <= t["frost_risk_temp"] else "media",
                action="Activar sistemas antihelada o protección de brotes si temperatura baja de 2 °C.",
            ))

        if w["etc"] is not None and w["dha"] is not None and w["dha"] < w["etc"] * 0.6:
            items.append(PreventionItem(
                risk="future_water_stress",
                label="Estrés hídrico futuro",
                priority="alta",
                action="El balance hídrico es deficitario. Aumentar frecuencia de riego preventivo.",
            ))
        elif w["humidity"] < t["humidity_low"]:
            items.append(PreventionItem(
                risk="future_water_stress",
                label="Estrés hídrico potencial",
                priority="media",
                action="Humedad baja. Monitorizar tensión de suelo y anticipar riego.",
            ))

        if w["humidity"] >= t["humidity_high"] and w["temp_max"] >= 15:
            items.append(PreventionItem(
                risk="mildiu_risk",
                label="Riesgo de mildiu",
                priority="alta" if w["humidity"] >= 85 else "media",
                action="Condiciones óptimas para mildiu. Revisar cobertura fungicida (cobre o sistémico).",
            ))

        if w["temp_max"] >= t["heat_stress_temp"]:
            items.append(PreventionItem(
                risk="heat_stress",
                label="Estrés térmico",
                priority="media",
                action="Evitar intervenciones agresivas (poda verde, tratamientos) en horas de máximo calor.",
            ))

        if not items:
            items.append(PreventionItem(
                risk="none",
                label="Sin riesgos detectados",
                priority="baja",
                action="Mantener seguimiento rutinario. Revisar estado de la planta y de la cobertura del suelo.",
            ))

        return items


    def _build_explanation(
        self,
        irr: IrrigationPlan,
        climate: ClimateSummary,
        crop: CropStatus,
        prev: list[PreventionItem],
        state: SharedState,
    ) -> str:
        region  = getattr(state, "ccaa", "la región analizada")
        period  = f"{state.start_date} a {state.end_date}" if (
            getattr(state, "start_date", None) and getattr(state, "end_date", None)
        ) else "el periodo analizado"

        assumed_note = ""
        if irr.assumed_values:
            assumed_note = (
                f"\nNota: los siguientes valores se han asumido por falta de datos: "
                f"{', '.join(irr.assumed_values)}."
            )

        high_prev = [p for p in prev if p.priority == "alta"]
        med_prev  = [p for p in prev if p.priority == "media"]

        prevention_lines = ""
        if high_prev:
            prevention_lines += "Atención prioritaria: " + "; ".join(p.label for p in high_prev) + ". "
        if med_prev:
            prevention_lines += "Vigilar también: " + "; ".join(p.label for p in med_prev) + "."

        phase_note = " (fase estimada por mes)" if crop.assumed else ""

        explanation = (
            f"Plan de manejo para {region} — {period}.\n\n"
            f"Clima: {climate.interpretation}\n\n"
            f"Riego: se recomiendan {irr.adjusted_liters} L/m² ({irr.adjustment_reason}).\n\n"
            f"Cultivo en fase de {crop.phase}{phase_note}. {crop.recommendation}\n\n"
            f"Prevención: {prevention_lines if prevention_lines else 'Sin riesgos destacados. Seguimiento rutinario.'}"
            f"{assumed_note}"
        )

        return explanation.strip()
    
    def _build_sms(self, irr, climate, prev, state) -> str:
        region = getattr(state, "ccaa", "—")

        top_prev = next((p for p in prev if p.priority == "alta"), None) or prev[0]
        warn_text = f"Alerta: {top_prev.label}" if top_prev.risk != "none" else "Sin alertas"

        sms = (
            f"AgroVid | {region} | "
            f"Riego: {irr.adjusted_liters} L/m2 | "
            f"{climate.condition} | "
            f"{warn_text}"
        )
        return sms[:160]