"""
agents/analysis.py — AnalysisAgent (Claude 기반 거시경제 분석)

Bounded Context: 수집된 데이터 + 컨텍스트 → 정량 분석 → EconomicSignal 반환.
동기 anthropic SDK를 asyncio executor로 래핑.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from functools import partial

from agents.base import BaseAgent
from domain.market_data import MarketData
from domain.signal import EconomicSignal, Signal

logger = logging.getLogger(__name__)

_JSON_PATTERN = re.compile(r"\{.*\}", re.DOTALL)

_USER_TEMPLATE = """\
다음 거시경제 데이터를 분석하고 투자 신호를 판단해줘.

시장 스냅샷: {market_context}

추가 컨텍스트: {context}

아래 JSON 형식으로만 응답해:
{{
  "signal": "BULLISH" | "NEUTRAL" | "BEARISH",
  "confidence": <float 0.0-1.0>,
  "rationale": "<2-3문장 근거>"
}}"""


class AnalysisAgent(BaseAgent):
    def __init__(self, api_key: str = "", model: str = "claude-sonnet-4-6") -> None:
        super().__init__("analysis", max_retries=2, timeout_sec=60.0)
        self._api_key = api_key
        self._model = model
        self._client = None  # lazy init

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    async def execute(self, market_data: MarketData, context: str = "") -> EconomicSignal:
        if not self._api_key:
            raise ValueError("AnalysisAgent: ANTHROPIC_API_KEY 없음")

        prompt = _USER_TEMPLATE.format(
            market_context=market_data.to_prompt_context(),
            context=context or "추가 컨텍스트 없음.",
        )

        # 동기 SDK → executor로 비동기 래핑
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            partial(
                self._get_client().messages.create,
                model=self._model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            ),
        )

        raw = message.content[0].text
        parsed = _parse_json(raw)
        logger.info(f"[analysis] signal={parsed.get('signal')} conf={parsed.get('confidence')}")

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
