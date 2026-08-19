from agents.base_agent import BaseAgent
from analytics.usage_analysis import UsageAnalyzer
from utils.helpers import convert_numpy_types


class UsageAgent(BaseAgent):

    def __init__(self):
        super().__init__("UsageAgent")

    def run(self, data=None):

        self.logger.info("Analyzing energy usage patterns...")

        analyzer = UsageAnalyzer()
        report = analyzer.generate_report()

        return convert_numpy_types(report)