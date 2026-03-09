"""
eco_system Orchestrator — Hub-and-spoke 패턴
1단계: 스포크 에이전트 병렬 실행 → 합의 도출
2단계: GuardrailAgent로 합의 검증 (프로필 설정 시)

usegit/patterns/hub-and-spoke.md 참조.
"""

import asyncio
import logging
from collections import Counter
from datetime import date

import anthropic
from core.schemas import AgentRequest, AgentResponse, AgentRole, Signal, EcoResult
from core.config import config
from agents.base import BaseAgent
from agents.research import ResearchAgent
from agents.analysis import AnalysisAgent

logger = logging.getLogger(__name__)


class Orchestrator:
    """Hub 역할: 스포크 에이전트를 병렬 실행하고 합의 도출"""

    def __init__(self):
        self.spokes: list[BaseAgent] = [
            ResearchAgent(),
            AnalysisAgent(),
        ]
        self.max_rounds: int = 2
        self.consensus_threshold: float = 0.80
        self.use_guardrail: bool = False
        self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    async def run(self, task: str, data: dict, context: str = "") -> EcoResult:
        request = AgentRequest(task=task, data=data, context=context)

        # 1단계: 스포크 병렬 실행
        logger.info(f"[Orchestrator] {len(self.spokes)}개 에이전트 병렬 실행")
        responses: list[AgentResponse] = await asyncio.gather(
            *[agent.run(request) for agent in self.spokes],
            return_exceptions=True,
        )

        valid = [r for r in responses if isinstance(r, AgentResponse)]
        errors = [r for r in responses if isinstance(r, Exception)]
        for err in errors:
            logger.warning(f"[Orchestrator] 에이전트 실패: {err}")

        consensus = self._consensus(valid)
        result = EcoResult(
            date=str(date.today()),
            consensus_signal=consensus["signal"],
            consensus_confidence=consensus["confidence"],
            agent_responses=valid,
            key_factors=consensus["key_factors"],
            summary=consensus["summary"],
        )

        # 2단계: Guardrail 검증 (프로필에서 활성화 시)
        if self.use_guardrail and valid:
            logger.info("[Orchestrator] Guardrail 검증 실행")
            try:
                from agents.guardrail import GuardrailAgent
                notes = GuardrailAgent.validate(result, data, self._client)
                result.guardrail_notes = notes
                logger.info(f"[Guardrail] {notes[:80]}")
            except Exception as e:
                logger.warning(f"[Guardrail] 실패: {e}")
                result.guardrail_notes = f"검증 실패: {e}"

        return result

    def _consensus(self, responses: list[AgentResponse]) -> dict:
        if not responses:
            return {
                "signal": Signal.NEUTRAL,
                "confidence": 0.0,
                "key_factors": [],
                "summary": "에이전트 응답 없음",
            }

        signal_counts = Counter(r.signal for r in responses)
        majority_signal = signal_counts.most_common(1)[0][0]
        agreeing = [r for r in responses if r.signal == majority_signal]
        avg_confidence = sum(r.confidence for r in agreeing) / len(agreeing)

        summary = (
            f"{majority_signal.value} 합의 "
            f"({len(agreeing)}/{len(responses)}명 동의, 신뢰도 {avg_confidence:.0%})"
        )
        return {
            "signal": majority_signal,
            "confidence": avg_confidence,
            "key_factors": [],
            "summary": summary,
        }
