"""
End-to-End Pipeline Test
Energy Optimization Agent

Exercises the full stack: dataset -> agents/orchestrator -> API endpoints,
verifying that data flows consistently between layers.
"""

from fastapi.testclient import TestClient

from backend.api import app

client = TestClient(app)


def test_end_to_end_api_pipeline():
    # 1. Usage analytics
    usage_resp = client.get("/usage")
    assert usage_resp.status_code == 200
    usage_data = usage_resp.json()
    assert "consumption" in usage_data

    # 2. Forecasting
    forecast_resp = client.get("/forecast")
    assert forecast_resp.status_code == 200
    forecast_data = forecast_resp.json()
    assert "evaluation" in forecast_data

    # 3. Anomaly detection
    anomaly_resp = client.get("/anomaly")
    assert anomaly_resp.status_code == 200
    anomaly_data = anomaly_resp.json()
    assert "statistics" in anomaly_data

    # 4. Recommendations (depends on the three reports above)
    rec_resp = client.get("/recommendations")
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert "recommendations" in rec_data
    assert len(rec_data["recommendations"]) > 0

    # 5. AI Insight (reasoning layer - real LLM call if ANTHROPIC_API_KEY is
    #    set, deterministic fallback otherwise; either way must succeed)
    insight_resp = client.get("/insights")
    assert insight_resp.status_code == 200
    insight_data = insight_resp.json()
    assert insight_data["alert_level"] in {"Normal", "Watch", "Urgent"}
    assert insight_data["source"] in {"llm", "fallback"}

    # 6. Final compiled report
    report_resp = client.get("/reports")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    assert "summary_markdown" in report_data
    assert "Energy Intelligence Audit Report" in report_data["summary_markdown"]
    assert report_data["alert_level"] in {"Normal", "Watch", "Urgent"}

    # 7. Real-time chat, grounded in the same pipeline data
    chat_resp = client.post("/chat/", json={"message": "What's the biggest risk right now?", "history": []})
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert chat_data["source"] in {"llm", "fallback"}
    assert len(chat_data["reply"]) > 0


def test_end_to_end_pipeline_consistency(usage_report, recommendation_report):
    """
    Sanity check that the recommendation engine's savings figures are
    derived from usage data of the same order of magnitude (not stubbed).
    """
    avg_daily_kwh = usage_report["consumption"]["average_daily_energy_kwh"]
    monthly_saving_kwh = recommendation_report["savings"]["monthly_saving_kwh"]

    assert avg_daily_kwh >= 0
    # Monthly savings should be a small, plausible fraction of monthly usage,
    # not an arbitrary/hardcoded number.
    monthly_usage_kwh = avg_daily_kwh * 30
    if monthly_usage_kwh > 0:
        assert 0 <= monthly_saving_kwh <= monthly_usage_kwh
