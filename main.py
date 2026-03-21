from agents.observation_agent import ObservationAgent
from agents.inference_agent import InferenceAgent
from agents.prediction_agent import PredictionAgent
from models.shared_state import create_shared_state
from datetime import date
from pprint import pprint
import os

def main():
    shared_state = create_shared_state(
        station = "B013X",
        start_date = date(2024, 1, 21),
        end_date = date(2024, 1, 21)
    )

    token = os.environ.get("HF_TOKEN")

    observation_agent = ObservationAgent()
    inference_agent = InferenceAgent()
    prediction_agent = PredictionAgent()

    shared_state = observation_agent.run(shared_state)  
    shared_state = inference_agent.run(shared_state)
    shared_state = prediction_agent.run(shared_state)

    pprint(shared_state, sort_dicts = False)

if __name__ == "__main__":
    main()

