"""
Test Usage Agent
Energy Optimization Agent
"""

from agents.usage_agent import UsageAgent
from backend.cache import CacheManager


def test_usage_agent_returns_real_report():
    cached = CacheManager.get("usage")
    if cached:
        report = cached
    else:
        report = UsageAgent().execute(None)
        CacheManager.set("usage", report)

    assert isinstance(report, dict)
    assert "consumption" in report
    assert "average_daily_energy_kwh" in report["consumption"]
    # Values must be native python floats, not numpy types
    assert isinstance(report["consumption"]["average_daily_energy_kwh"], float)
