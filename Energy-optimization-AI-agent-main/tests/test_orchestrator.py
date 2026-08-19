"""
Test Agent Orchestrator
Energy Optimization Agent
"""

from agents.orchestrator import AgentOrchestrator


def test_orchestrator_initializes_all_agents():
    orchestrator = AgentOrchestrator()

    assert orchestrator.usage_agent is not None
    assert orchestrator.forecasting_agent is not None
    assert orchestrator.anomaly_agent is not None
    assert orchestrator.recommendation_agent is not None
    assert orchestrator.insight_agent is not None
    assert orchestrator.reporting_agent is not None


def test_orchestrator_pipeline_shape(
    usage_report, forecast_report, anomaly_report, recommendation_report,
    insight_report, reporting_report
):
    """
    The session-scoped fixtures already exercised the full agent chain and
    populated CacheManager, so we assert on those results directly instead
    of re-running the (expensive) Prophet / Isolation Forest fits again.
    """
    for report in (
        usage_report, forecast_report, anomaly_report,
        recommendation_report, insight_report, reporting_report
    ):
        assert isinstance(report, dict)

    assert "consumption" in usage_report
    assert "evaluation" in forecast_report
    assert "statistics" in anomaly_report
    assert "savings" in recommendation_report
    assert "alert_level" in insight_report
    assert insight_report["alert_level"] in {"Normal", "Watch", "Urgent"}
    assert "summary_markdown" in reporting_report
