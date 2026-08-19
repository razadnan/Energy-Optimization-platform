from agents.base_agent import BaseAgent
from services.report_generator import ReportGenerator
from utils.helpers import convert_numpy_types


class ReportingAgent(BaseAgent):

    def __init__(self):
        super().__init__("ReportingAgent")

    def run(self, data):

        self.logger.info("Preparing final energy optimization report...")

        generator = ReportGenerator(data)
        report = generator.generate_report()

        return convert_numpy_types(report)