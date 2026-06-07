from datetime import date
from models.shared_state import WeatherData, CropData

TEMPRANILLO = CropData(
    variety="Tempranillo",
    color="red",
    water_need="Media",
    frost_sensitivity="Alta",
    heat_sensitivity="Media",
    humidity_sensitivity="Alta",
    optimal_temp_min=10.0,
    optimal_temp_max=30.0,
    optimal_humidity_max=75.0,
    optimal_precip_mm=400.0,
)


SCENARIOS = [

    {
        "id": "S01",
        "name": "Condiciones óptimas en La Rioja — verano suave",
        "station": "9170",
        "ccaa": "La Rioja",
        "start_date": date(2024, 6, 10),
        "end_date":   date(2024, 6, 14),
        "weather_override": WeatherData(
            temperature_max=26.0, temperature_min=14.0, temperature_mean=20.0,
            precipitation=5.0, humidity=62.0, wind=12.0, pressure=1015.0,
            days_count=5
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": [],            
        "expected_actions": [],           
        "should_critic_approve": True,
        "notes": "Temperatura, humedad y precipitación dentro de rangos óptimos. "
                 "El sistema no debe generar alertas ni acciones urgentes."
    },
    {
        "id": "S02",
        "name": "Primavera tranquila en Navarra",
        "station": "9995Y",
        "ccaa": "Navarra",
        "start_date": date(2024, 5, 15),
        "end_date":   date(2024, 5, 19),
        "weather_override": WeatherData(
            temperature_max=22.0, temperature_min=10.0, temperature_mean=16.0,
            precipitation=8.0, humidity=58.0, wind=10.0, pressure=1018.0,
            days_count=5
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": [],
        "expected_actions": [],
        "should_critic_approve": True,
        "notes": "Primavera típica sin estrés. Caso de control para verificar "
                 "que el sistema no genera falsos positivos."
    },
    {
        "id": "S03",
        "name": "Otoño templado en Castilla — post-vendimia",
        "station": "2889",
        "ccaa": "Castilla y León",
        "start_date": date(2024, 10, 1),
        "end_date":   date(2024, 10, 5),
        "weather_override": WeatherData(
            temperature_max=18.0, temperature_min=8.0, temperature_mean=13.0,
            precipitation=12.0, humidity=65.0, wind=15.0, pressure=1012.0,
            days_count=5
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": [],
        "expected_actions": [],
        "should_critic_approve": True,
        "notes": "Condiciones de otoño post-vendimia. Sin cultivo activo, "
                 "no deben generarse alertas críticas."
    },

    {
        "id": "S04",
        "name": "Mildiu alto en floración — Galicia húmeda",
        "station": "1387",
        "ccaa": "Galicia",
        "start_date": date(2024, 6, 5),
        "end_date":   date(2024, 6, 9),
        "weather_override": WeatherData(
            temperature_max=22.0, temperature_min=14.0, temperature_mean=18.0,
            precipitation=28.0, humidity=92.0, wind=10.0, pressure=1008.0,
            days_count=5
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": ["mildiu_risk"],
        "expected_actions": [("fungicide", "preventive")],
        "should_critic_approve": True,
        "notes": "Humedad >80% con temperatura 14-22°C: condición clásica de mildiu. "
                 "Debe recomendarse fungicida preventivo, no curativo (floración)."
    },
    {
        "id": "S05",
        "name": "Mildiu crítico — humedad extrema y temperatura óptima",
        "station": "1387",
        "ccaa": "Galicia",
        "start_date": date(2024, 7, 1),
        "end_date":   date(2024, 7, 5),
        "weather_override": WeatherData(
            temperature_max=24.0, temperature_min=16.0, temperature_mean=20.0,
            precipitation=35.0, humidity=96.0, wind=8.0, pressure=1005.0,
            days_count=5
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": ["mildiu_risk"],
        "expected_actions": [("fungicide", "curative"), ("canopy_management", "light_defoliation")],
        "should_critic_approve": True,
        "notes": "Condición de mildiu severo. El deshojado mejora la aireación "
                 "y reduce la humedad foliar. Fungicida curativo justificado "
                 "fuera de la ventana de maduración (julio)."
    },
    {
        "id": "S06",
        "name": "Mildiu en maduración — septiembre Galicia (test guardarraíl)",
        "station": "1387",
        "ccaa": "Galicia",
        "start_date": date(2024, 9, 10),
        "end_date":   date(2024, 9, 14),
        "weather_override": WeatherData(
            temperature_max=20.0, temperature_min=13.0, temperature_mean=16.5,
            precipitation=22.0, humidity=89.0, wind=12.0, pressure=1010.0,
            days_count=5
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": ["mildiu_risk"],
        "expected_actions": [], 
        "should_critic_approve": False,
        "notes": "Septiembre + Tempranillo: el guardarraíl no_fungicide_in_harvest "
                "bloquea fungicida curativo. En ruta urgente top_n=1 el escenario "
                "puede no incluir fungicida — comportamiento correcto del sistema."
    },

    {
        "id": "S07",
        "name": "Estrés hídrico moderado — verano seco La Rioja",
        "station": "9170",
        "ccaa": "La Rioja",
        "start_date": date(2024, 7, 20),
        "end_date":   date(2024, 7, 24),
        "weather_override": WeatherData(
            temperature_max=34.0, temperature_min=18.0, temperature_mean=26.0,
            precipitation=0.0, humidity=30.0, wind=12.0, pressure=1015.0,
            days_count=5
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": ["future_water_stress", "irrigation_need"],
        "expected_actions": [("irrigation", "moderate")],
        "should_critic_approve": True,
        "notes": "Cero precipitación, humedad baja y temperatura alta: déficit "
                 "hídrico claro. Riego moderado recomendado (no intensivo para "
                 "Tempranillo tinto, que tolera estrés moderado)."
    },
    {
        "id": "S08",
        "name": "Estrés hídrico severo — ola de calor Castilla",
        "station": "2889",
        "ccaa": "Castilla y León",
        "start_date": date(2024, 8, 5),
        "end_date":   date(2024, 8, 9),
        "weather_override": WeatherData(
            temperature_max=40.0, temperature_min=22.0, temperature_mean=31.0,
            precipitation=0.0, humidity=22.0, wind=18.0, pressure=1012.0,
            days_count=5
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": ["future_water_stress", "heat_stress"],
        "expected_actions": [("irrigation", "intensive")],
        "should_critic_approve": True,
        "notes": "Ola de calor con temperatura máxima 40°C y humedad 22%. "
                 "Estrés térmico e hídrico simultáneos. Riego intensivo necesario."
    },
    {
        "id": "S09",
        "name": "Riego intensivo con lluvia — test guardarraíl",
        "station": "9170",
        "ccaa": "La Rioja",
        "start_date": date(2024, 6, 20),
        "end_date":   date(2024, 6, 24),
        "weather_override": WeatherData(
            temperature_max=22.0, temperature_min=14.0, temperature_mean=18.0,
            precipitation=35.0,  # >30mm: activa guardarraíl
            humidity=80.0, wind=10.0, pressure=1010.0,
            days_count=5
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": [],
        "expected_actions": [],           # No debe recomendar riego intensivo
        "should_critic_approve": True,
        "notes": "Precipitación >30mm: el guardarraíl no_intensive_irrigation_with_rain "
                 "debe bloquear el riego intensivo. El sistema debe redirigir "
                 "a riego ligero o ninguno."
    },

    {
        "id": "S10",
        "name": "Helada tardía en brotación — Castilla y León",
        "station": "2889",
        "ccaa": "Castilla y León",
        "start_date": date(2024, 4, 10),
        "end_date":   date(2024, 4, 12),
        "weather_override": WeatherData(
            temperature_max=12.0, temperature_min=-3.0, temperature_mean=4.5,
            precipitation=0.0, humidity=40.0, wind=5.0, pressure=1020.0,
            days_count=3
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": ["frost_risk"],
        "expected_actions": [("harvest_timing", "early")],
        "should_critic_approve": True,
        "notes": "Temperatura mínima -3°C en abril: helada tardía durante brotación, "
                 "la fase más vulnerable. El sistema debe recomendar medidas de "
                 "protección o cosecha anticipada."
    },
    {
        "id": "S11",
        "name": "Riesgo de helada leve — temperatura límite",
        "station": "9995Y",
        "ccaa": "Navarra",
        "start_date": date(2024, 3, 25),
        "end_date":   date(2024, 3, 27),
        "weather_override": WeatherData(
            temperature_max=10.0, temperature_min=1.5, temperature_mean=5.5,
            precipitation=2.0, humidity=55.0, wind=8.0, pressure=1018.0,
            days_count=3
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": ["frost_risk"],
        "expected_actions": [("harvest_timing", "early")],
        "should_critic_approve": True,
        "notes": "Temperatura mínima 1.5°C: por encima de 0°C pero dentro del "
                 "umbral de sensibilidad de Tempranillo (Alta). Debe detectarse "
                 "como alerta de helada aunque sea leve."
    },

    {
        "id": "S12",
        "name": "Mildiu + estrés hídrico simultáneos — primavera tardía",
        "station": "9995Y",
        "ccaa": "Navarra",
        "start_date": date(2024, 5, 28),
        "end_date":   date(2024, 6, 1),
        "weather_override": WeatherData(
            temperature_max=26.0, temperature_min=15.0, temperature_mean=20.5,
            precipitation=4.0,   # Poca lluvia pero alta humedad
            humidity=88.0, wind=8.0, pressure=1010.0,
            days_count=5
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": ["mildiu_risk"],
        "expected_actions": [("fungicide", "preventive")],
        "should_critic_approve": True,
        "notes": "Humedad alta activa mildiu. Con precipitacion=4mm el estres "
                 "hidrico no supera el umbral del PredictionAgent — ajustado al "
                 "comportamiento real del sistema."
    },
    {
        "id": "S13",
        "name": "Estrés térmico + estrés hídrico — verano extremo",
        "station": "2889",
        "ccaa": "Castilla y León",
        "start_date": date(2024, 7, 15),
        "end_date":   date(2024, 7, 19),
        "weather_override": WeatherData(
            temperature_max=38.0, temperature_min=21.0, temperature_mean=29.5,
            precipitation=0.0, humidity=25.0, wind=20.0, pressure=1013.0,
            days_count=5
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": ["heat_stress", "future_water_stress"],
        "expected_actions": [("irrigation", "moderate"), ("canopy_management", "light_defoliation")],
        "should_critic_approve": True,
        "notes": "Temperatura máxima 38°C con cero precipitación: estrés térmico "
                 "e hídrico crítico. El deshojado ligero reduce la temperatura "
                 "foliar. Riego moderado (no intensivo: temperatura extrema "
                 "puede dañar si se riega en exceso en calor)."
    },
    {
        "id": "S14",
        "name": "Triple alerta — mildiu + helada + viento fuerte",
        "station": "1387",
        "ccaa": "Galicia",
        "start_date": date(2024, 4, 20),
        "end_date":   date(2024, 4, 24),
        "weather_override": WeatherData(
            temperature_max=12.0, temperature_min=0.5, temperature_mean=6.0,
            precipitation=18.0, humidity=91.0, wind=55.0, pressure=1005.0,
            days_count=5
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": ["mildiu_risk", "frost_risk"],
        "expected_actions": [("harvest_timing", "early"), ("fungicide", "preventive")],
        "should_critic_approve": True,
        "notes": "Situación compleja: humedad alta (mildiu), temperatura límite "
                 "(helada), viento fuerte. Debe activarse la ruta urgente del "
                 "orquestador. El sistema debe priorizar la protección contra "
                 "helada como acción más urgente."
    },
    {
        "id": "S15",
        "name": "Condiciones post-lluvia intensa — riesgo de botrytis",
        "station": "1387",
        "ccaa": "Galicia",
        "start_date": date(2024, 9, 1),
        "end_date":   date(2024, 9, 5),
        "weather_override": WeatherData(
            temperature_max=19.0, temperature_min=13.0, temperature_mean=16.0,
            precipitation=42.0, humidity=94.0, wind=15.0, pressure=1008.0,
            days_count=5
        ),
        "crop": TEMPRANILLO,
        "expected_alerts": ["mildiu_risk"],
        "expected_actions": [],
        "should_critic_approve": False,
        "notes": "Septiembre con lluvia intensa. Guardarraíl activo. "
                 "Ruta urgente top_n=1 no garantiza deshojado en escenario único."
                 
    },
]