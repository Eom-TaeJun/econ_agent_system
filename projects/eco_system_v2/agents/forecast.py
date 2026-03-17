"""
agents/forecast.py — ForecastAgent (Claude 기반 전망 특화)

시장 데이터 + 다른 에이전트 신호를 바탕으로 포워드 전망 생성.
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
다음 거시경제 데이터를 바탕으로 향후 1~3개월 전망을 분석해줘.

시장 스냅샷: {market_context}

추가 컨텍스트: {context}

다음 관점에서 분석해:
1. 매크로 모멘텀: 현재 추세가 지속될 가능성
2. 리스크 요인: 전망을 뒤집을 수 있는 이벤트
3. 주요 동인: 향후 시장을 주도할 요인

아래 JSON 형식으로만 응답해:
{{
  "signal": "BULLISH" | "NEUTRAL" | "BEARISH",
  "confidence": <float 0.0-1.0>,
  "rationale": "<2-3문장 전망 요약>",
  "key_drivers": "<주요 동인 1줄>",
  "risks": "<핵심 리스크 1줄>"
}}"""


class ForecastAgent(BaseAgent):
    def __init__(self, api_key: str = "", model: str = "claude-sonnet-4-6") -> None:
        super().__init__("forecast", max_retries=2, timeout_sec=60.0)
        self._api_key = api_key
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    async def execute(self, market_data: MarketData, context: str = "") -> EconomicSignal:
        if not self._api_key:
            raise ValueError("ForecastAgent: ANTHROPIC_API_KEY 없음")

        prompt = _USER_TEMPLATE.format(
            market_context=market_data.to_prompt_context(),
            context=context or "추가 컨텍스트 없음.",
        )

        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            partial(
                self._get_client().messages.create,
                model=self._model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            ),
        )

        raw = message.content[0].text
        parsed = _parse_json(raw)
        logger.info(f"[forecast] signal={parsed.get('signal')} conf={parsed.get('confidence')}")

        return EconomicSignal(
            agent=self.name,
            signal=Signal(parsed.get("signal", "NEUTRAL")),
            confidence=float(parsed.get("confidence", 0.5)),
            rationale=parsed.get("rationale", raw[:300]),
        )


def _parse_json(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = _JSON_PATTERN.search(text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return {}
        return {}
