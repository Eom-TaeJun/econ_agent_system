"""
agents/orchestrator.py — Orchestrator (Hub)

Hub-and-spoke 패턴:
  - Hub: Orchestrator (이 파일)
  - Spokes: ResearchAgent, AnalysisAgent

합의 로직은 domain/consensus.py에 위임. 이 파일은 조율만 담당.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date

from agents.base import BaseAgent
from agents.research import ResearchAgent
from agents.analysis import AnalysisAgent
from domain.consensus import ConsensusService
from domain.market_data import MarketData
from domain.signal import EconomicSignal

logger = logging.getLogger(__name__)


class EcoResult:
    """파이프라인 최종 결과 컨테이너"""

    def __init__(
        self,
        consensus: EconomicSignal,
        agent_signals: list[EconomicSignal],
        market_data: MarketData,
    ) -> None:
        self.date = str(date.today())
        self.consensus = consensus
        self.agent_signals = agent_signals
        self.market_data = market_data

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "consensus_signal": self.consensus.signal.value,
            "consensus_confidence": self.consensus.confidence,
            "consensus_rationale": self.consensus.rationale,
            "agent_signals": [s.to_dict() for s in self.agent_signals],
            "market_data": self.market_data.to_dict(),
        }


class Orchestrator:
    """
    Hub: 스포크 에이전트를 asyncio.gather로 병렬 실행 후
    ConsensusService로 합의 도출.

    quick 모드: AnalysisAgent만 실행 (30초 이내)
    full 모드: ResearchAgent + AnalysisAgent 병렬
    """

    def __init__(
        self,
        anthropic_api_key: str = "",
        perplexity_api_key: str = "",
        claude_model: str = "claude-sonnet-4-6",
        perplexity_model: str = "sonar",
    ) -> None:
        self._analysis = AnalysisAgent(api_key=anthropic_api_key, model=claude_model)
        self._research = ResearchAgent(api_key=perplexity_api_key, model=perplexity_model)

    def _get_spokes(self, quick: bool) -> list[BaseAgent]:
        if quick:
            return [self._analysis]
        return [self._research, self._analysis]

    async def run(
        self,
        market_data: MarketData,
        context: str = "",
        quick: bool = False,
    ) -> EcoResult:
        spokes = self._get_spokes(quick)
        mode = "quick" if quick else "full"
        logger.info(f"[Orchestrator] {mode} 모드 — {len(spokes)}개 에이전트 병렬 실행")

        raw_results = await asyncio.gather(
            *[spoke.run(market_data, context) for spoke in spokes],
            return_exceptions=True,
        )

        valid: list[EconomicSignal] = []
        for r in raw_results:
            if isinstance(r, EconomicSignal):
                valid.append(r)
            else:
                logger.warning(f"[Orchestrator] 에이전트 실패: {r}")

        consensus = ConsensusService.compute(valid)
        logger.info(
            f"[Orchestrator] 합의 완료: {consensus.signal.value} "
            f"(conf={consensus.confidence:.0%})"
        )

        return EcoResult(
            consensus=consensus,
            agent_signals=valid,
            market_data=market_data,
        )
