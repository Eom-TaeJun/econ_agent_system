"""
agents/debate.py — DebateAgent (Claude 기반 합의 도전)

ADR: DebateAgent는 순차 실행 — 다른 에이전트 신호를 입력으로 받아야 함.
흐름: Analysis+Research+Quant (병렬) → Debate (순차)
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
다른 에이전트들의 분석 결과를 검토하고 합의에 도전해줘.

시장 스냅샷: {market_context}

에이전트 분석 결과:
{agent_signals}

추가 컨텍스트: {context}

역할: Devil's Advocate (악마의 변호인)
1. 다른 에이전트들의 합의가 틀릴 수 있는 이유를 찾아라
2. 반대 시나리오의 가능성을 평가하라
3. 최종적으로 합의에 동의하든 반대하든, 명확한 근거를 제시하라

아래 JSON 형식으로만 응답해:
{{
  "signal": "BULLISH" | "NEUTRAL" | "BEARISH",
  "confidence": <float 0.0-1.0>,
  "rationale": "<2-3문장 종합 판단>",
  "challenges": "<합의에 대한 핵심 도전/반론 1-2줄>",
  "agreement_ratio": <float 0.0-1.0, 원래 합의와 얼마나 동의하는지>
}}"""


class DebateAgent(BaseAgent):
    def __init__(self, api_key: str = "", model: str = "claude-sonnet-4-6") -> None:
        super().__init__("debate", max_retries=2, timeout_sec=60.0)
        self._api_key = api_key
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    async def execute(self, market_data: MarketData, context: str = "") -> EconomicSignal:
        """
        context에 다른 에이전트 신호 요약이 포함되어야 함.
        Orchestrator가 context를 조합해서 전달.
        """
        if not self._api_key:
            raise ValueError("DebateAgent: ANTHROPIC_API_KEY 없음")

        prompt = _USER_TEMPLATE.format(
            market_context=market_data.to_prompt_context(),
            agent_signals=context,
            context="",
        )

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
        logger.info(
            f"[debate] signal={parsed.get('signal')} "
            f"conf={parsed.get('confidence')} "
            f"agreement={parsed.get('agreement_ratio')}"
        )

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
