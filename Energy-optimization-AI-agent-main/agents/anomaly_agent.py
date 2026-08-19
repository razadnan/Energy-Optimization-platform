from agents.base_agent import BaseAgent
from models.anomaly_detection import AnomalyDetectionModel
from utils.helpers import convert_numpy_types


class AnomalyAgent(BaseAgent):

    def __init__(self):
        super().__init__("AnomalyAgent")

    def run(self, data=None):

        self.logger.info("Detecting anomalies using Isolation Forest...")

        model = AnomalyDetectionModel()
        report = model.run_pipeline()

        return convert_numpy_types(report)