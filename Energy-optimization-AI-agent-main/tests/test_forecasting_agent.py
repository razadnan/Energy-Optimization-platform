"""
Test Forecasting Agent
Energy Optimization Agent
"""

from agents.forecasting_agent import ForecastingAgent
from backend.cache import CacheManager


def test_forecasting_agent_returns_real_report():
    cached = CacheManager.get("forecast", max_age_seconds=43200)
    if cached:
        report = cached
    else:
        report = ForecastingAgent().execute(None)
        CacheManager.set("forecast", report)

    assert isinstance(report, dict)
    assert "evaluation" in report
    assert report["evaluation"]["model_name"] == "Facebook Prophet"
