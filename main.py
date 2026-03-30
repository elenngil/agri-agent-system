# main.py
from agents.observation_agent import ObservationAgent
from agents.inference_agent import InferenceAgent
from agents.prediction_agent import PredictionAgent
from agents.risk_agent import RiskAgent
from agents.deliberative_agent import DeliberativeAgent
from agents.explanation_agent import ExplanationAgent
from agents.daily_plan_agent import DailyPlanAgent
from smolagents import InferenceClientModel
from models import shared_state
from models.shared_state import SharedState 
from tools.aemet_stations import station_to_ccaa
from tools.aemet_api import AemetError
from datetime import date
from pprint import pprint


def main():
    station = "9995Y"

    try:
        ccaa = station_to_ccaa(station)
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Si usas dataclass:
    shared_state = SharedState(
        station=station,
        start_date=date(2024, 7, 22),
        end_date=date(2024, 7, 26),  # Rango de 5 días para probar agregación
        ccaa=ccaa
    )
    
    observation_agent = ObservationAgent()
    inference_agent = InferenceAgent()
    prediction_agent = PredictionAgent()
    risk_agent = RiskAgent()
    deliberative_agent = DeliberativeAgent()
    explanation_agent = ExplanationAgent(model=InferenceClientModel("gpt-3.5-turbo"))
    daily_plan_agent = DailyPlanAgent()

    try:
        # Pipeline
        print(f"Ejecutando para {ccaa} (estación {station})...\n")
        
        shared_state = observation_agent.run(shared_state)
        print("✓ Observación completada")
        
        shared_state = inference_agent.run(shared_state)
        print("✓ Inferencia completada")
        
        shared_state = prediction_agent.run(shared_state)
        print("✓ Predicción completada")

        shared_state = risk_agent.run(shared_state)
        print("✓ Evaluación de riesgos completada")

        shared_state = deliberative_agent.run(shared_state)
        print("✓ Deliberación completada")

        shared_state = explanation_agent.run(shared_state)
        print("✓ Explicación generada")

        shared_state = daily_plan_agent.run(shared_state)
        print("✓ Plan diario generado")


        print("\n" + "="*50)
        print("RESULTADO FINAL")
        print("="*50)
        
        # Si usas dataclass, convertir a dict para pprint
        if hasattr(shared_state, '__dataclass_fields__'):
            from dataclasses import asdict
            #pprint(asdict(shared_state), sort_dicts=False)
            print("\n" + "=" * 50)
            print("RESUMEN EXPLICATIVO")
            print("=" * 50)
            print(shared_state.explanation["summary"])

            print("\n" + "=" * 50)
            print("MOTIVO DE LA DECISIÓN")
            print("=" * 50)
            print(shared_state.explanation["decision_why"]["short_reason"])

            print("\n" + "=" * 50)
            print("CONFIANZA")
            print("=" * 50)
            print(
                f"{shared_state.explanation['confidence']['label'].upper()} "
                f"({shared_state.explanation['confidence']['score']})"
            )

            print("\n" + "=" * 50)
            print("SMS")
            print("=" * 50)
            print(shared_state.explanation["sms_text"])

            print("\n" + "=" * 50)
            print("PLAN DIARIO")
            print("=" * 50)
            print("\nSMS:")
            print(shared_state.daily_plan.sms)

            print("\nExplicación:")
            print(shared_state.daily_plan.explanation)
            


        else:
            #pprint(shared_state, sort_dicts=False)
            print("\n" + "=" * 50)
            print("RESUMEN EXPLICATIVO")
            print("=" * 50)
            print(shared_state.explanation["summary"])

            print("\n" + "=" * 50)
            print("MOTIVO DE LA DECISIÓN")
            print("=" * 50)
            print(shared_state.explanation["decision_why"]["short_reason"])


            print("\n" + "=" * 50)
            print("CONFIANZA")
            print("=" * 50)
            print(
                f"{shared_state.explanation['confidence']['label'].upper()} "
                f"({shared_state.explanation['confidence']['score']})"
            )

            print("\n" + "=" * 50)
            print("SMS")
            print("=" * 50)
            print(shared_state.explanation["sms_text"])

            print("\n" + "=" * 50)
            print("PLAN DIARIO")
            print("=" * 50)
            print("\nSMS:")
            print(shared_state.daily_plan.sms)

            print("\nExplicación:")
            print(shared_state.daily_plan.explanation)
            
    except AemetError as e:
        print(f"Error de AEMET: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")
        raise
if __name__ == "__main__":
    main()