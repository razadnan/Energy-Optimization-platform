"""
Chat Service
=========================================================
Powers the real-time "Ask the Energy Assistant" chat.

Perceives  : the user's question, prior conversation turns, AND the
             current usage / forecast / anomaly / recommendation /
             insight reports (the same data every dashboard page shows).
Reasons    : an LLM answers using ONLY that grounded context - it is
             explicitly instructed not to invent numbers - so answers
             about "what's going on" stay tied to the real pipeline
             output instead of hallucinating figures.
Acts       : returns a conversational reply; because the system prompt
             is rebuilt from live cache data on every call, the
             assistant's answers change automatically as the underlying
             data changes (new anomalies, new forecast, etc.) without
             any extra wiring.

Degrades to a deterministic, still-grounded reply (built from the same
report dict via simple string templating) when no LLM is configured or
the call fails, so the chat never just errors out on the user.
"""

import json

from services.llm_client import LLMClient
from services.logger import setup_logger

logger = setup_logger("ChatService")

MAX_HISTORY_TURNS = 10  # keep the prompt small; older turns are dropped

SYSTEM_PROMPT_TEMPLATE = """You are the "Energy Assistant" embedded in a \
household energy optimization dashboard. You help the homeowner \
understand what the AI pipeline found and how to act on it - usage \
patterns, the demand forecast, detected anomalies, savings \
recommendations, and the overall risk level.

Rules:
- Answer ONLY using the CURRENT PIPELINE DATA given below. Never invent \
  numbers, dates, or findings that are not present in it.
- If the data doesn't contain what's needed to answer, say so plainly \
  instead of guessing.
- Be conversational and concise (2-5 sentences unless the user asks for \
  detail). This is a chat, not a report.
- When asked "how do I fix/solve X", ground your suggestion in the \
  recommendations list already present in the data, don't invent new ones.

CURRENT PIPELINE DATA:
{context_json}
"""

class ChatService:
    def __init__(self):
        self.client = LLMClient()

    def answer(self, message: str, history: list, reports: dict) -> dict:
        """
        message : the user's latest question (str)
        history : list of {"role": "user"|"assistant", "content": str}
        reports : {"usage": ..., "forecast": ..., "anomaly": ...,
                   "recommendation": ..., "insight": ...}
        """
        if not self.client.is_available():
            return {
                "reply": self._fallback_reply(
                    message,
                    reports,
                    "no LLM API key is configured, so this is a templated response rather than a reasoned answer. Set GEMINI_API_KEY to enable full conversational reasoning."
                ),
                "source": "fallback",
            }

        try:
            system_prompt = self._build_system_prompt(reports)
            reply = self._call_llm(message, history, system_prompt)
            return {"reply": reply, "source": "llm"}
        except Exception as exc:
            logger.error(f"Chat LLM call failed, falling back: {exc}")
            err_msg = str(exc)
            if "429" in err_msg or "quota" in err_msg.lower() or "limit" in err_msg.lower() or "exhausted" in err_msg.lower():
                reason = "Gemini API rate limit or daily quota exceeded (429 Too Many Requests). Please wait a moment or check your API key's tier."
            else:
                reason = f"Gemini API call failed: {err_msg}"
            return {
                "reply": self._fallback_reply(message, reports, reason),
                "source": "fallback",
            }

    def _build_system_prompt(self, reports: dict) -> str:
        context = self._summarize_context(reports)
        return SYSTEM_PROMPT_TEMPLATE.format(
            context_json=json.dumps(context, indent=2, default=str)
        )

    def _summarize_context(self, reports: dict) -> dict:
        """
        Trims each report down to the fields a conversational answer
        actually needs, keeping the prompt small instead of dumping full
        30-day forecast tables / all anomaly records into every turn.
        """
        usage = reports.get("usage") or {}
        forecast = reports.get("forecast") or {}
        anomaly = reports.get("anomaly") or {}
        recommendation = reports.get("recommendation") or {}
        insight = reports.get("insight") or {}

        return {
            "usage": {
                "summary": usage.get("summary"),
                "consumption": usage.get("consumption"),
                "peak_usage": usage.get("peak_usage"),
                "weekday_weekend": usage.get("weekday_weekend"),
            },
            "forecast": {
                "summary": forecast.get("summary"),
                "evaluation": forecast.get("evaluation"),
                "statistics": forecast.get("statistics"),
            },
            "anomaly": {
                "statistics": anomaly.get("statistics"),
                "top_high_risk_records": (anomaly.get("high_risk_records") or [])[:5],
            },
            "recommendation": {
                "recommendations": recommendation.get("recommendations"),
                "savings": recommendation.get("savings"),
                "co2": recommendation.get("co2"),
            },
            "insight": {
                "alert_level": insight.get("alert_level"),
                "primary_concern": insight.get("primary_concern"),
                "reasoning": insight.get("reasoning"),
            },
        }

    def _call_llm(self, message: str, history: list, system_prompt: str) -> str:
        trimmed_history = (history or [])[-MAX_HISTORY_TURNS:]
        convo = "\n".join(
            f"{turn.get('role', 'user').upper()}: {turn.get('content', '')}"
            for turn in trimmed_history
        )
        prompt = (
            f"{convo}\nUSER: {message}\nASSISTANT:" if convo
            else f"USER: {message}\nASSISTANT:"
        )
        return self.client.generate(prompt, system=system_prompt)

    def _fallback_reply(self, message: str, reports: dict, reason: str = None) -> str:
        """
        A deterministic, still-grounded reply used only when no LLM is
        configured or the call failed. Answers the most common intents
        with simple keyword matching over the real report data.
        """
        insight = reports.get("insight") or {}
        anomaly = (reports.get("anomaly") or {}).get("statistics", {})
        savings = (reports.get("recommendation") or {}).get("savings", {})
        recs = (reports.get("recommendation") or {}).get("recommendations", [])

        lowered = message.lower()

        if any(w in lowered for w in ["risk", "urgent", "alert", "concern"]):
            body = (
                f"Current alert level: {insight.get('alert_level', 'Normal')}. "
                f"{insight.get('primary_concern', 'No specific concern flagged.')}"
            )
        elif any(w in lowered for w in ["anomaly", "anomalies", "spike", "unusual"]):
            body = (
                f"{anomaly.get('anomaly_records', 0)} anomalies detected "
                f"({anomaly.get('anomaly_percentage', 0)}% of records), "
                f"including {anomaly.get('critical_anomalies', 0)} critical."
            )
        elif any(w in lowered for w in ["save", "saving", "solve", "fix", "reduce", "recommend"]):
            if recs:
                top = recs[0]
                body = (
                    f"Top recommendation: [{top.get('priority')}] "
                    f"{top.get('recommendation')} "
                    f"(~{top.get('estimated_saving_percent')}% saving). "
                    f"Estimated monthly savings: ₹{savings.get('estimated_monthly_savings_rupees', 0):.2f}."
                )
            else:
                body = "No recommendations are available yet."
        else:
            body = (
                f"Alert level is {insight.get('alert_level', 'Normal')}. "
                "Ask about anomalies, savings, or risk for more detail."
            )

        if reason:
            fallback_note = f"(AI chat is running in fallback mode - {reason})"
        else:
            fallback_note = (
                "(AI chat is running in fallback mode - no LLM API key is configured, "
                "so this is a templated response rather than a reasoned answer. Set "
                "GEMINI_API_KEY to enable full conversational reasoning.)"
            )

        return f"{body}\n\n{fallback_note}"
