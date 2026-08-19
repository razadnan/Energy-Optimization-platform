"""
Test Reporting Agent
Energy Optimization Agent
"""

from agents.reporting_agent import ReportingAgent


def test_reporting_agent_returns_markdown(
    usage_report, forecast_report, anomaly_report, recommendation_report, insight_report
):
    agent = ReportingAgent()
    report = agent.execute({
        "usage": usage_report,
        "forecast": forecast_report,
        "anomaly": anomaly_report,
        "recommendation": recommendation_report,
        "insight": insight_report,
    })

    assert isinstance(report, dict)
    assert "summary_markdown" in report
    assert "Energy Intelligence Audit Report" in report["summary_markdown"]
    assert report["status"] == "Report generated successfully"
    assert report["alert_level"] == insight_report["alert_level"]
    # The AI reasoning section should be embedded in the markdown
    assert "AI Insight Agent" in report["summary_markdown"]
