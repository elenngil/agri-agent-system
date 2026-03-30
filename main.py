from orchestrator import Orchestrator
from smolagents import InferenceClientModel
from models.shared_state import SharedState
from tools.aemet_stations import station_to_ccaa
from tools.aemet_api import AemetError
from datetime import date


def main():
    station = "9995Y"

    try:
        ccaa = station_to_ccaa(station)
    except ValueError as e:
        print(f"Error: {e}")
        return

    shared_state = SharedState(
        station=station,
        start_date=date(2024, 7, 22),
        end_date=date(2024, 7, 26),
        ccaa=ccaa
    )

    orchestrator = Orchestrator(
        model=InferenceClientModel("gpt-3.5-turbo")
    )

    try:
        print(f"Ejecutando para {ccaa} (estación {station})...\n")

        shared_state = orchestrator.run(shared_state)

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