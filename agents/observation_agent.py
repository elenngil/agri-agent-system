from smolagents import CodeAgent, InferenceClientModel
from tools.weather_data import get_climate_summary
from tools.soil_data import get_soil_multiplier
from tools.crop_data import get_crop_data
from models.shared_state import create_shared_state

class ObservationAgent:
    def __init__(self):
        model = InferenceClientModel()

        self.agent = CodeAgent(
            model=model, 
            name="ObservationAgent", 
            description="Agente encargado de recopilar y procesar datos climáticos, del suelo y del cultivo para proporcionar información relevante a los demás agentes del sistema.",
            tools = [get_climate_summary, get_soil_multiplier, get_crop_data]
            )
        
    def run(self, shared_state: dict) -> dict:
        station = shared_state["station"]
        start_date = shared_state["start_date"]
        end_date = shared_state["end_date"]

        prompt = f"""
        Usa las tools que he proporcionado para obtener:
        - datos climáticos de la estación {station} entre las fechas {start_date} y {end_date}
        - el multiplicador de riego basado en el tipo de suelo de la estación {station}
        - información relevante sobre el tipo de cultivo de la estación {station}

        Devuelve un diccionario con las siguientes claves: "weather_data", "soil_multiplier" y "crop_data", con la información obtenida de cada tool.
        """

        result = self.agent.run(prompt)

        shared_state["weather_data"] = result.get("weather_data")
        shared_state["soil_multiplier"] = result.get("soil_multiplier")
        shared_state["crop_data"] = result.get("crop_data")

        return shared_state

