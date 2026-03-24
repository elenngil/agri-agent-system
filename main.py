# main.py
from agents.observation_agent import ObservationAgent
from agents.inference_agent import InferenceAgent
from agents.prediction_agent import PredictionAgent
from models.shared_state import SharedState 
from tools.aemet_stations import station_to_ccaa
from tools.aemet_api import AemetError
from datetime import date
from pprint import pprint
def main():
    station = "B013X"

    try:
        ccaa = station_to_ccaa(station)
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Si usas dataclass:
    shared_state = SharedState(
        station=station,
        start_date=date(2024, 1, 21),
        end_date=date(2024, 1, 25),  # Rango de 5 días para probar agregación
        ccaa=ccaa
    )
    
    # Si sigues con dict:
    # shared_state = create_shared_state(
    #     station=station,
    #     start_date=date(2024, 1, 21),
    #     end_date=date(2024, 1, 25)
    # )
    # shared_state["ccaa"] = ccaa
    # Inicializar agentes
    observation_agent = ObservationAgent()
    inference_agent = InferenceAgent()
    prediction_agent = PredictionAgent()
    try:
        # Pipeline
        print(f"Ejecutando para {ccaa} (estación {station})...\n")
        
        shared_state = observation_agent.run(shared_state)
        print("✓ Observación completada")
        
        shared_state = inference_agent.run(shared_state)
        print("✓ Inferencia completada")
        
        shared_state = prediction_agent.run(shared_state)
        print("✓ Predicción completada")
        
        # TODO: Añadir cuando estén implementados
        # shared_state = risk_agent.run(shared_state)
        # shared_state = deliberative_agent.run(shared_state)
        # shared_state = explainer_agent.run(shared_state)
        
        print("\n" + "="*50)
        print("RESULTADO FINAL")
        print("="*50)
        
        # Si usas dataclass, convertir a dict para pprint
        if hasattr(shared_state, '__dataclass_fields__'):
            from dataclasses import asdict
            pprint(asdict(shared_state), sort_dicts=False)
        else:
            pprint(shared_state, sort_dicts=False)
            
    except AemetError as e:
        print(f"Error de AEMET: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")
        raise
if __name__ == "__main__":
    main()