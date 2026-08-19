"""
Multi-Agent Orchestrator
Coordinates all agents.
"""

from agents.usage_agent import UsageAgent
from agents.forecasting_agent import ForecastingAgent
from agents.anomaly_agent import AnomalyAgent
from agents.recommendation_agent import RecommendationAgent
from agents.insight_agent import InsightAgent
from agents.reporting_agent import ReportingAgent

from services.logger import setup_logger


class AgentOrchestrator:

    def __init__(self):

        self.logger = setup_logger("Orchestrator")

        self.usage_agent = UsageAgent()
        self.forecasting_agent = ForecastingAgent()
        self.anomaly_agent = AnomalyAgent()
        self.recommendation_agent = RecommendationAgent()
        self.insight_agent = InsightAgent()
        self.reporting_agent = ReportingAgent()

    def run_pipeline(self, raw_data):

        self.logger.info("Starting Energy Optimization Pipeline")

        usage_result = self.usage_agent.execute(raw_data)

        forecast_result = self.forecasting_agent.execute(
            usage_result
        )

        anomaly_result = self.anomaly_agent.execute(
            {
                "usage": usage_result,
                "forecast": forecast_result
            }
        )

        recommendation_result = self.recommendation_agent.execute(
            {
                "usage": usage_result,
                "forecast": forecast_result,
                "anomaly": anomaly_result
            }
        )

        insight_result = self.insight_agent.execute(
            {
                "usage": usage_result,
                "forecast": forecast_result,
                "anomaly": anomaly_result,
                "recommendation": recommendation_result
            }
        )

        report_result = self.reporting_agent.execute(
            {
                "usage": usage_result,
                "forecast": forecast_result,
                "anomaly": anomaly_result,
                "recommendation": recommendation_result,
                "insight": insight_result
            }
        )

        self.logger.info("Pipeline completed successfully.")

        return {
            "usage": usage_result,
            "forecast": forecast_result,
            "anomaly": anomaly_result,
            "recommendation": recommendation_result,
            "insight": insight_result,
            "report": report_result
        }
