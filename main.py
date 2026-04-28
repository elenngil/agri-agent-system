from datetime import date
import logging
from orchestrator import Orchestrator
from models.shared_state import SharedState
from tools.aemet_stations import station_to_ccaa
from tools.aemet_api import AemetError

import os
from dotenv import load_dotenv
from smolagents import InferenceClientModel

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/agri_agent.log"),
    ]
)

logger = logging.getLogger(__name__)

def main():
    station = "9995Y"

    load_dotenv()

    try:
        ccaa = station_to_ccaa(station)
    except ValueError as e:
        logger.error("Error con la estación: %s", e)
        return

    shared_state = SharedState(
        station=station,
        start_date=date(2024, 7, 22),
        end_date=date(2024, 7, 26),
        ccaa=ccaa
    )

    model = InferenceClientModel(
        model_id="Qwen/Qwen2.5-72B-Instruct",
        token=os.environ["HF_TOKEN"],
    )

    orchestrator = Orchestrator(model=model)

    logger.info("Iniciando pipeline para %s (estación %s)", ccaa, station)

    try:
        shared_state = orchestrator.run(shared_state)

        logger.info("Pipeline completado — región: %s", shared_state.ccaa)

        print("\n" + "=" * 50)
        print("RESULTADO FINAL")
        print("=" * 50)

        print("\n" + "=" * 50)
        print("RESUMEN EXPLICATIVO")
        print("=" * 50)
        print(shared_state.explanation["summary"])

        print("\n" + "=" * 50)
        print("MOTIVO DE LA DECISIÓN")
        print("=" * 50)
        print(shared_state.explanation["recommendation_reasoning"])

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
        logger.error("Error AEMET: %s", e)

    except Exception:
        logger.exception("Error inesperado")
        raise


if __name__ == "__main__":
    main()