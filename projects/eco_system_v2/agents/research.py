"""
agents/research.py — ResearchAgent (Perplexity 기반 거시경제 리서치)

Bounded Context: 최신 거시경제 뉴스 리서치 → EconomicSignal 반환.
"""

from __future__ import annotations

import json
import logging
import re

import httpx

from agents.base import BaseAgent
from domain.market_data import MarketData
from domain.signal import EconomicSignal, Signal

logger = logging.getLogger(__name__)

_JSON_PATTERN = re.compile(r"\{.*\}", re.DOTALL)

_SYSTEM_PROMPT = (
    "You are a macroeconomic research analyst. "
    "Analyze current global economic conditions and provide a structured JSON assessment."
)

_USER_TEMPLATE = """\
Market snapshot: {market_context}

Additional context: {context}

Analyze the current macroeconomic conditions and respond ONLY with valid JSON:
{{
  "signal": "BULLISH" | "NEUTRAL" | "BEARISH",
  "confidence": <float 0.0-1.0>,
  "rationale": "<2-3 sentence summary>"
}}"""


class ResearchAgent(BaseAgent):
    def __init__(self, api_key: str = "", model: str = "sonar") -> None:
        super().__init__("research", max_retries=2, timeout_sec=45.0)
        self._api_key = api_key
        self._model = model

    async def execute(self, market_data: MarketData, context: str = "") -> EconomicSignal:
        if not self._api_key:
            raise ValueError("ResearchAgent: PERPLEXITY_API_KEY 없음")

        prompt = _USER_TEMPLATE.format(
            market_context=market_data.to_prompt_context(),
            context=context or "No additional context.",
        )

        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]

        parsed = _parse_json(raw)
        logger.info(f"[research] signal={parsed.get('signal')} conf={parsed.get('confidence')}")

        return EconomicSignal(
            agent=self.name,
            signal=Signal(parsed.get("signal", "NEUTRAL")),
            confidence=float(parsed.get("confidence", 0.5)),
            rationale=parsed.get("rationale", raw[:300]),
        )


def _parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = _JSON_PATTERN.search(text)
        if match:
            return json.loads(match.group())
        return {}
