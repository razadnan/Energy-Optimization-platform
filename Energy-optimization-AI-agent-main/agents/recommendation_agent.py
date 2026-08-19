from agents.base_agent import BaseAgent
from services.recommendation_engine import RecommendationEngine
from utils.helpers import convert_numpy_types


class RecommendationAgent(BaseAgent):

    def __init__(self):
        super().__init__("RecommendationAgent")

    def run(self, data):

        self.logger.info("Generating energy-saving recommendations...")

        usage_report = data.get("usage")
        forecast_report = data.get("forecast")
        anomaly_report = data.get("anomaly")

        engine = RecommendationEngine(
            usage_report=usage_report,
            forecast_report=forecast_report,
            anomaly_report=anomaly_report
        )
        report = engine.run_pipeline()

        return convert_numpy_types(report)