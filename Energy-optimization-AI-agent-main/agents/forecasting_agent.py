from agents.base_agent import BaseAgent
from models.forecasting import ForecastingModel
from utils.helpers import convert_numpy_types


class ForecastingAgent(BaseAgent):

    def __init__(self):
        super().__init__("ForecastingAgent")

    def run(self, data=None):

        self.logger.info("Generating energy consumption forecast using Prophet...")

        model = ForecastingModel()
        report = model.run_pipeline()

        return convert_numpy_types(report)