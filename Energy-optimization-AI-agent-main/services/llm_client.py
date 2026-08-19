"""
LLM Client
Thin wrapper around the LLM APIs (Gemini and Anthropic) so agents don't need to know the
SDK's call signature. Used by InsightAgent and ChatService.
"""

import httpx
from backend.config import config
from services.logger import setup_logger

logger = setup_logger("LLMClient")


class LLMClient:
    """
    Minimal wrapper: generate(prompt) -> str.

    Reads the API keys from Config. If Gemini key is set, routes via HTTP REST to Gemini.
    Otherwise falls back to Anthropic API if Anthropic key is set.
    """

    def __init__(self, model: str = None, max_tokens: int = None):
        self._model_override = model
        self.max_tokens = max_tokens or config.INSIGHT_MAX_TOKENS
        self._client = None
        self._client_key = None

        if config.GEMINI_API_KEY:
            self._client = "gemini"
        elif config.ANTHROPIC_API_KEY:
            self._client = "anthropic"

        if not self._client:
            logger.info(
                "Neither GEMINI_API_KEY nor ANTHROPIC_API_KEY set - LLM reasoning will fall back."
            )

    @property
    def model(self) -> str:
        return self._model_override or config.INSIGHT_MODEL

    def is_available(self) -> bool:
        return self._client is not None

    def generate(self, prompt: str, system: str = None) -> str:
        """
        Returns plain text from the model. Uses Gemini if GEMINI_API_KEY is configured,
        otherwise falls back to Anthropic Claude.
        """
        gemini_key = config.GEMINI_API_KEY
        if gemini_key:
            return self._generate_gemini(prompt, system, gemini_key)

        anthropic_key = config.ANTHROPIC_API_KEY
        if anthropic_key:
            return self._generate_anthropic(prompt, system, anthropic_key)

        raise RuntimeError(
            "LLM client not configured: set GEMINI_API_KEY or ANTHROPIC_API_KEY to enable LLM reasoning."
        )

    def _generate_gemini(self, prompt: str, system: str, api_key: str) -> str:
        model_name = self.model
        # Map any legacy Claude model name to Gemini if the model wasn't updated
        if "claude" in model_name:
            model_name = "gemini-3.1-flash-lite"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": api_key
        }
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": self.max_tokens,
                "temperature": 0.2
            }
        }
        
        if system:
            payload["systemInstruction"] = {
                "parts": [{"text": system}]
            }

        try:
            logger.info(f"Sending request to Gemini API (Model: {model_name})...")
            response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            # Extract response text
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()
        except Exception as exc:
            logger.error(f"Gemini LLM call failed: {exc}")
            raise

    def _generate_anthropic(self, prompt: str, system: str, api_key: str) -> str:
        try:
            import anthropic
        except ImportError:
            logger.error("anthropic package not installed - run 'pip install anthropic'.")
            raise RuntimeError("Anthropic library missing.")

        if not isinstance(self._client, anthropic.Anthropic) or self._client_key != api_key:
            self._client = anthropic.Anthropic(api_key=api_key)
            self._client_key = api_key
            logger.info("Anthropic client initialized successfully.")

        model_name = self.model
        if "gemini" in model_name:
            model_name = "claude-3-5-sonnet-20241022"

        kwargs = {
            "model": model_name,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        try:
            logger.info(f"Sending request to Anthropic API (Model: {model_name})...")
            response = self._client.messages.create(**kwargs)
            return "".join(
                block.text for block in response.content if block.type == "text"
            ).strip()
        except Exception as exc:
            logger.error(f"Anthropic LLM call failed: {exc}")
            raise
