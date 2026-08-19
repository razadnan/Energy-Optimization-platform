"""
Insight Agent
=========================================================
The reasoning stage of the pipeline.

Perceives  : the four structured reports produced upstream
             (usage, forecast, anomaly, recommendation)
Reasons    : an LLM judgment call - not a fixed rule - about how urgent
             the situation is and which single finding matters most.
             Given the same inputs, the specific alert level on a
             borderline case can vary, because it is a genuine judgment
             rather than a hardcoded threshold.
Acts       : writes that decision back into the pipeline output
             (alert_level, primary_concern) so the report and dashboard
             can change what they show as a result.

Degrades gracefully to a deterministic rule-based summary if no
ANTHROPIC_API_KEY is configured or the LLM call fails, so the pipeline
never breaks for lack of a key - but the fallback path is explicitly
labeled so it's never mistaken for the reasoning path.
"""

import json

from agents.base_agent import BaseAgent
from services.llm_client import LLMClient
from utils.helpers import convert_numpy_types


ALERT_LEVELS = {"Normal", "Watch", "Urgent"}

SYSTEM_PROMPT = """You are an energy efficiency analyst reviewing an automated \
household energy audit. You will be given four structured summaries: usage \
statistics, a demand forecast, anomaly detection results, and cost-saving \
recommendations.

Decide, using judgment rather than a fixed rule, how urgent this \
household's situation is, and which single finding matters most for the \
homeowner to act on first. Base your reasoning only on the numbers \
provided - never invent figures that are not in the data.

Respond with ONLY a JSON object, no other text, in this exact shape:
{
  "alert_level": "Normal" | "Watch" | "Urgent",
  "primary_concern": "<one short sentence>",
  "reasoning": "<2-3 sentences explaining the judgment>",
  "executive_summary": "<4-6 sentence plain-language summary for a homeowner>"
}
"""


class InsightAgent(BaseAgent):
    """
    The one agent in the pipeline whose output is genuinely
    non-deterministic: it makes a judgment call, not a lookup.
    """

    def __init__(self):
        super().__init__("InsightAgent")
        self.client = LLMClient()

    def run(self, data):
        usage = data.get("usage") or {}
        forecast = data.get("forecast") or {}
        anomaly = data.get("anomaly") or {}
        recommendation = data.get("recommendation") or {}

        if not self.client.is_available():
            self.logger.warning(
                "LLM unavailable - using deterministic fallback instead of "
                "an LLM judgment."
            )
            return self._fallback(anomaly)

        prompt = self._build_prompt(usage, forecast, anomaly, recommendation)

        try:
            raw = self.client.generate(prompt, system=SYSTEM_PROMPT)
            parsed = self._parse_response(raw)
        except Exception as exc:
            self.logger.error(f"InsightAgent LLM call failed, falling back: {exc}")
            return self._fallback(anomaly)

        return convert_numpy_types(parsed)

    def _build_prompt(self, usage, forecast, anomaly, recommendation) -> str:
        payload = {
            "usage_summary": usage.get("summary"),
            "usage_consumption": usage.get("consumption"),
            "forecast_evaluation": forecast.get("evaluation"),
            "anomaly_statistics": anomaly.get("statistics"),
            "recommendation_savings": recommendation.get("savings"),
            "top_recommendations": (recommendation.get("recommendations") or [])[:3],
        }
        return (
            "Here is the structured audit data:\n\n"
            f"{json.dumps(payload, indent=2, default=str)}\n\n"
            "Return the JSON object described in your instructions."
        )

    def _parse_response(self, raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        parsed = json.loads(text)

        alert_level = parsed.get("alert_level", "Normal")
        if alert_level not in ALERT_LEVELS:
            alert_level = "Normal"

        return {
            "alert_level": alert_level,
            "primary_concern": parsed.get("primary_concern", ""),
            "reasoning": parsed.get("reasoning", ""),
            "executive_summary": parsed.get("executive_summary", ""),
            "source": "llm",
        }

    def _fallback(self, anomaly: dict) -> dict:
        """
        Deterministic degrade path used only when no API key is configured
        or the LLM call fails. Keeps the pipeline runnable end-to-end
        without a key - clearly labeled so it is never mistaken for the
        reasoning path.
        """
        stats = anomaly.get("statistics", {})
        critical = stats.get("critical_anomalies", 0) or 0
        anomaly_pct = stats.get("anomaly_percentage", 0) or 0

        if critical > 0:
            alert_level = "Urgent"
            concern = f"{critical} critical anomalies detected in recent usage."
        elif anomaly_pct > 5:
            alert_level = "Watch"
            concern = f"Anomaly rate is elevated at {anomaly_pct:.1f}% of records."
        else:
            alert_level = "Normal"
            concern = "No significant irregularities detected."

        return {
            "alert_level": alert_level,
            "primary_concern": concern,
            "reasoning": "Deterministic fallback rule (LLM unavailable).",
            "executive_summary": (
                "Automated LLM summary unavailable without an API key. "
                "See the Usage, Forecast, Anomaly, and Recommendation "
                "sections for full detail."
            ),
            "source": "fallback",
        }
