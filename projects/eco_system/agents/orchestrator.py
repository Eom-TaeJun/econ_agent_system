"""
eco_system Orchestrator — Hub-and-spoke 패턴
EIMAS agents/orchestrator.py 참조 (경량화)

Hub-and-spoke: 오케스트레이터가 허브, research/analysis가 스포크.
usegit/patterns/hub-and-spoke.md 참조.
"""

import asyncio
import logging
from collections import Counter

from core.schemas import AgentRequest, AgentResponse, AgentRole, Signal, EcoResult
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

    async def run(self, task: str, data: dict, context: str = "") -> EcoResult:
        request = AgentRequest(task=task, data=data, context=context)

        # 병렬 실행 (hub-and-spoke)
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
        from datetime import date
        return EcoResult(
            date=str(date.today()),
            consensus_signal=consensus["signal"],
            consensus_confidence=consensus["confidence"],
            agent_responses=valid,
            key_factors=consensus["key_factors"],
            summary=consensus["summary"],
        )

    def _consensus(self, responses: list[AgentResponse]) -> dict:
        if not responses:
            return {
                "signal": Signal.NEUTRAL,
                "confidence": 0.0,
                "key_factors": [],
                "summary": "에이전트 응답 없음",
            }

        # 다수결 신호
        signal_counts = Counter(r.signal for r in responses)
        majority_signal = signal_counts.most_common(1)[0][0]

        # 평균 신뢰도 (다수결 신호에 동의한 에이전트만)
        agreeing = [r for r in responses if r.signal == majority_signal]
        avg_confidence = sum(r.confidence for r in agreeing) / len(agreeing)

        summary = f"{majority_signal.value} 합의 ({len(agreeing)}/{len(responses)}명 동의, 신뢰도 {avg_confidence:.0%})"

        return {
            "signal": majority_signal,
            "confidence": avg_confidence,
            "key_factors": [],
            "summary": summary,
        }
