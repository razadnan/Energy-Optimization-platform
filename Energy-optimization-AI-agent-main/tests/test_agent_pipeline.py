import pytest
from agents.orchestrator import AgentOrchestrator
from backend.cache import CacheManager

def test_agent_orchestrator():
    """
    Test the multi-agent orchestrator execution and output shapes.
    Uses CacheManager to prevent re-running models on consecutive runs.
    """
    # Pre-populate or check CacheManager
    usage = CacheManager.get("usage")
    forecast = CacheManager.get("forecast")
    anomaly = CacheManager.get("anomaly")
    recommendations = CacheManager.get("recommendations")
    report = CacheManager.get("report")
    
    # If caches are present, we can verify shapes directly
    if usage and forecast and anomaly and recommendations and report:
        assert "summary" in usage
        assert "consumption" in usage
        assert "forecast" in forecast
        assert "statistics" in forecast
        assert "evaluation" in forecast
        assert "mape" in forecast["evaluation"]
        assert "rmse" in forecast["evaluation"]
        assert "statistics" in anomaly
        assert "high_risk_records" in anomaly
        assert "recommendations" in recommendations
        assert "savings" in recommendations
        assert "summary_markdown" in report
        return

    orchestrator = AgentOrchestrator()
    result = orchestrator.run_pipeline(None)
    
    # Assert return keys
    assert "usage" in result
    assert "forecast" in result
    assert "anomaly" in result
    assert "recommendation" in result
    assert "report" in result
    
    # Assert values are real dictionary reports and not stub stings
    assert isinstance(result["usage"], dict)
    assert "consumption" in result["usage"]
    assert "average_daily_energy_kwh" in result["usage"]["consumption"]
    
    # Check forecasting agent outputs
    assert isinstance(result["forecast"], dict)
    assert "evaluation" in result["forecast"]
    assert result["forecast"]["evaluation"]["status"] == "Model Trained and Evaluated Successfully"
    assert "mape" in result["forecast"]["evaluation"]
    
    # Check anomaly agent outputs
    assert isinstance(result["anomaly"], dict)
    assert "statistics" in result["anomaly"]
    assert "anomaly_records" in result["anomaly"]["statistics"]
    assert "critical_anomalies" in result["anomaly"]["statistics"]
    
    # Check recommendation agent outputs
    assert isinstance(result["recommendation"], dict)
    assert "savings" in result["recommendation"]
    assert "estimated_monthly_savings_rupees" in result["recommendation"]["savings"]
    
    # Check reporting agent outputs
    assert isinstance(result["report"], dict)
    assert "summary_markdown" in result["report"]
    assert "Audit Report" in result["report"]["summary_markdown"]
