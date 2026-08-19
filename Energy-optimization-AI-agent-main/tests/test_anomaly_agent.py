"""
Test Anomaly Agent
Energy Optimization Agent
"""

from agents.anomaly_agent import AnomalyAgent
from backend.cache import CacheManager


def test_anomaly_agent_returns_real_report():
    cached = CacheManager.get("anomaly", max_age_seconds=43200)
    if cached:
        report = cached
    else:
        report = AnomalyAgent().execute(None)
        CacheManager.set("anomaly", report)

    assert isinstance(report, dict)
    assert "statistics" in report
    assert "anomaly_records" in report["statistics"]
