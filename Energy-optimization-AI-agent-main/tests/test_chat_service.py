"""
Test Chat Service
Energy Optimization Agent

Covers both the LLM path (mocked, no network required) and the
deterministic fallback path used when no ANTHROPIC_API_KEY is configured
or the LLM call fails - the chat must never hard-error either way.
"""

from unittest.mock import MagicMock

from services.chat_service import ChatService


SAMPLE_REPORTS = {
    "usage": {
        "summary": {"total_records": 1000},
        "consumption": {"average_daily_energy_kwh": 12.5},
        "peak_usage": {"peak_hour": 19},
        "weekday_weekend": {"weekday_average_kw": 1.1, "weekend_average_kw": 1.4},
    },
    "forecast": {
        "summary": {"trend_direction": "Increasing"},
        "evaluation": {"model_name": "Facebook Prophet", "mape": 8.2, "rmse": 0.4},
        "statistics": {"average_predicted_energy": 13.0},
    },
    "anomaly": {
        "statistics": {
            "anomaly_records": 12,
            "anomaly_percentage": 1.2,
            "critical_anomalies": 2,
        },
        "high_risk_records": [],
    },
    "recommendation": {
        "recommendations": [
            {"category": "HVAC", "priority": "High", "recommendation": "Reduce AC hours",
             "estimated_saving_percent": 8.0}
        ],
        "savings": {"estimated_monthly_savings_rupees": 450.0},
        "co2": {"estimated_monthly_co2_reduction_kg": 20.0},
    },
    "insight": {
        "alert_level": "Watch",
        "primary_concern": "Anomaly rate is elevated.",
        "reasoning": "2 critical anomalies detected this period.",
    },
}


def test_chat_fallback_when_no_llm_configured():
    service = ChatService()
    service.client._client = None  # force unavailable

    result = service.answer("What's the biggest risk right now?", [], SAMPLE_REPORTS)

    assert result["source"] == "fallback"
    assert "Watch" in result["reply"]


def test_chat_fallback_answers_savings_questions():
    service = ChatService()
    service.client._client = None

    result = service.answer("How can I reduce my energy costs?", [], SAMPLE_REPORTS)

    assert result["source"] == "fallback"
    assert "Reduce AC hours" in result["reply"]


def test_chat_uses_llm_when_available():
    service = ChatService()
    mock_client = MagicMock()
    mock_client.is_available.return_value = True
    mock_client.generate.return_value = "Your biggest risk is the elevated anomaly rate."
    service.client = mock_client

    result = service.answer("What's going on with my anomalies?", [], SAMPLE_REPORTS)

    assert result["source"] == "llm"
    assert "anomaly rate" in result["reply"]
    mock_client.generate.assert_called_once()

    # The system prompt passed to generate() must be grounded in the real
    # data, not a generic prompt - this is what prevents hallucinated numbers.
    _, kwargs = mock_client.generate.call_args
    assert "Watch" in kwargs["system"]
    assert "critical_anomalies" in kwargs["system"]


def test_chat_falls_back_on_llm_error():
    service = ChatService()
    mock_client = MagicMock()
    mock_client.is_available.return_value = True
    mock_client.generate.side_effect = RuntimeError("simulated failure")
    service.client = mock_client

    result = service.answer("Any risks?", [], SAMPLE_REPORTS)

    assert result["source"] == "fallback"


def test_chat_respects_conversation_history_length():
    service = ChatService()
    mock_client = MagicMock()
    mock_client.is_available.return_value = True
    mock_client.generate.return_value = "ok"
    service.client = mock_client

    long_history = [
        {"role": "user", "content": f"question {i}"} for i in range(30)
    ]
    service.answer("latest question", long_history, SAMPLE_REPORTS)

    prompt_arg = mock_client.generate.call_args[0][0]
    # Only the most recent MAX_HISTORY_TURNS should appear in the prompt
    assert "question 0" not in prompt_arg
    assert "question 29" in prompt_arg
