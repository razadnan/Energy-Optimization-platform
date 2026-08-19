"""
Test Insight Agent
Energy Optimization Agent

Covers both paths: the LLM reasoning path (mocked, so tests don't require
a real API key or network access) and the deterministic fallback path
(used when no ANTHROPIC_API_KEY is configured or the LLM call fails).
"""

import json
from unittest.mock import patch, MagicMock

from agents.insight_agent import InsightAgent, ALERT_LEVELS


SAMPLE_DATA = {
    "usage": {
        "summary": {"total_records": 1000},
        "consumption": {"average_daily_energy_kwh": 12.5},
    },
    "forecast": {
        "evaluation": {"model_name": "Facebook Prophet", "mape": 8.2, "rmse": 0.4}
    },
    "anomaly": {
        "statistics": {
            "total_records": 1000,
            "anomaly_records": 12,
            "anomaly_percentage": 1.2,
            "critical_anomalies": 2,
            "high_anomalies": 4,
            "medium_anomalies": 6,
        }
    },
    "recommendation": {
        "recommendations": [
            {"category": "HVAC", "priority": "High", "recommendation": "Reduce AC hours",
             "estimated_saving_percent": 8.0}
        ],
        "savings": {"estimated_monthly_savings_rupees": 450.0},
    },
}


def test_insight_agent_fallback_when_no_llm_configured():
    """
    With no ANTHROPIC_API_KEY set, the agent must not crash - it should
    degrade to the deterministic fallback and label it as such.
    """
    agent = InsightAgent()
    agent.client._client = None  # force "unavailable" regardless of env

    result = agent.run(SAMPLE_DATA)

    assert result["source"] == "fallback"
    assert result["alert_level"] in ALERT_LEVELS
    # 2 critical anomalies in the sample data -> fallback rule should flag Urgent
    assert result["alert_level"] == "Urgent"
    assert "critical anomalies" in result["primary_concern"]


def test_insight_agent_uses_llm_response_when_available():
    """
    Mocks the LLM client so this test is deterministic and requires no
    network access, while still exercising the real parsing logic.
    """
    agent = InsightAgent()

    fake_llm_json = json.dumps({
        "alert_level": "Watch",
        "primary_concern": "Anomaly rate is above baseline this week.",
        "reasoning": "Anomaly percentage exceeds the normal range for this household.",
        "executive_summary": "Overall usage is stable but a few unusual spikes occurred.",
    })

    mock_client = MagicMock()
    mock_client.is_available.return_value = True
    mock_client.generate.return_value = fake_llm_json
    agent.client = mock_client

    result = agent.run(SAMPLE_DATA)

    assert result["source"] == "llm"
    assert result["alert_level"] == "Watch"
    assert result["primary_concern"] == "Anomaly rate is above baseline this week."
    mock_client.generate.assert_called_once()


def test_insight_agent_falls_back_on_llm_error():
    """
    If the LLM call raises (timeout, bad key, rate limit, malformed JSON),
    the agent must still return a usable result instead of propagating
    the exception - the pipeline should never break for lack of an LLM.
    """
    agent = InsightAgent()

    mock_client = MagicMock()
    mock_client.is_available.return_value = True
    mock_client.generate.side_effect = RuntimeError("simulated API failure")
    agent.client = mock_client

    result = agent.run(SAMPLE_DATA)

    assert result["source"] == "fallback"
    assert result["alert_level"] in ALERT_LEVELS


def test_insight_agent_rejects_invalid_alert_level():
    """
    If the LLM returns an alert_level outside the allowed set, the parser
    must not pass it through unchanged.
    """
    agent = InsightAgent()

    bad_json = json.dumps({
        "alert_level": "Catastrophic",  # not a valid level
        "primary_concern": "x",
        "reasoning": "x",
        "executive_summary": "x",
    })

    parsed = agent._parse_response(bad_json)
    assert parsed["alert_level"] == "Normal"
