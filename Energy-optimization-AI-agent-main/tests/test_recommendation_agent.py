"""
Test Recommendation Agent
Energy Optimization Agent
"""

from agents.recommendation_agent import RecommendationAgent


def test_recommendation_agent_returns_real_report(usage_report, forecast_report, anomaly_report):
    agent = RecommendationAgent()
    report = agent.execute({
        "usage": usage_report,
        "forecast": forecast_report,
        "anomaly": anomaly_report,
    })

    assert isinstance(report, dict)
    assert "recommendations" in report
    assert "savings" in report
    assert len(report["recommendations"]) > 0
