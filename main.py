import logging_config  # PRIMERA línea — configura logging antes de todo
import logging

from datetime import date
from orchestrator import Orchestrator
from models.shared_state import SharedState
from tools.aemet_stations import station_to_ccaa
from tools.aemet_api import AemetError

import os
from dotenv import load_dotenv
from smolagents import InferenceClientModel

logger = logging.getLogger(__name__)


def main():
    station = "9995Y"

    try:
        ccaa = station_to_ccaa(station)
    except ValueError as e:
        logger.error("Estación no encontrada: %s", e)
        return

    shared_state = SharedState(
        station=station,
        start_date=date(2024, 7, 22),
        end_date=date(2024, 7, 26),
        ccaa=ccaa
    )

    load_dotenv()

    model = InferenceClientModel(
        model_id="Qwen/Qwen2.5-72B-Instruct",
        token=os.environ["HF_TOKEN"],
    )
    orchestrator = Orchestrator(model=model)

    try:
        logger.info("Iniciando pipeline para %s (estación %s)", ccaa, station)

        shared_state = orchestrator.run(shared_state)

        logger.info("Pipeline completado — región: %s", ccaa)

        print("\n" + "=" * 50)
        print("RESUMEN EXPLICATIVO")
        print("=" * 50)
        print(shared_state.explanation["summary"])

        print("\n" + "=" * 50)
        print("MOTIVO DE LA DECISION")
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

        print("\nExplicacion:")
        print(shared_state.daily_plan.explanation)

    except AemetError as e:
        logger.error("Error de AEMET: %s", e)
    except Exception as e:
        logger.exception("Error inesperado")
        raise


if __name__ == "__main__":
    main()