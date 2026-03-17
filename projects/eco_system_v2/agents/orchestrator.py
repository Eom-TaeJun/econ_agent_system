"""
agents/orchestrator.py — Orchestrator (Hub)

Hub-and-spoke 패턴:
  - Hub: Orchestrator (이 파일)
  - Spokes: AnalysisAgent, ResearchAgent, QuantAgent, ForecastAgent, DebateAgent

합의 로직은 domain/consensus.py에 위임. 이 파일은 조율만 담당.

모드:
  --quick:    AnalysisAgent만
  --full:     Analysis + Research + Quant (병렬) → Debate (순차)
  --forecast: full + ForecastAgent 추가
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date

from agents.base import BaseAgent
from agents.analysis import AnalysisAgent
from agents.research import ResearchAgent
from agents.quant import QuantAgent
from agents.forecast import ForecastAgent
from agents.debate import DebateAgent
from domain.consensus import ConsensusService
from domain.market_data import MarketData
from domain.regime import RegimeResult
from domain.risk import RiskMetrics
from domain.signal import EconomicSignal

logger = logging.getLogger(__name__)


class EcoResult:
    """파이프라인 최종 결과 컨테이너"""

    def __init__(
        self,
        consensus: EconomicSignal,
        agent_signals: list[EconomicSignal],
        market_data: MarketData,
        regime: RegimeResult | None = None,
        risk_metrics: RiskMetrics | None = None,
        debate_summary: str = "",
    ) -> None:
        self.date = str(date.today())
        self.consensus = consensus
        self.agent_signals = agent_signals
        self.market_data = market_data
        self.regime = regime
        self.risk_metrics = risk_metrics
        self.debate_summary = debate_summary

    def to_dict(self) -> dict:
        result = {
            "date": self.date,
            "consensus_signal": self.consensus.signal.value,
            "consensus_confidence": self.consensus.confidence,
            "consensus_rationale": self.consensus.rationale,
            "agent_signals": [s.to_dict() for s in self.agent_signals],
            "market_data": self.market_data.to_dict(),
        }
        if self.regime:
            result["regime"] = self.regime.to_dict()
        if self.risk_metrics:
            result["risk_metrics"] = self.risk_metrics.to_dict()
        if self.debate_summary:
            result["debate_summary"] = self.debate_summary
        return result


class Orchestrator:
    """
    Hub: 스포크 에이전트를 실행 후 ConsensusService로 합의 도출.

    quick 모드:    AnalysisAgent만 (30초 이내)
    full 모드:     Analysis + Research + Quant (병렬) → Debate (순차)
    forecast 모드: full + ForecastAgent
    """

    def __init__(
        self,
        anthropic_api_key: str = "",
        perplexity_api_key: str = "",
        claude_model: str = "claude-sonnet-4-6",
        perplexity_model: str = "sonar",
    ) -> None:
        self._anthropic_key = anthropic_api_key
        self._analysis = AnalysisAgent(api_key=anthropic_api_key, model=claude_model)
        self._research = ResearchAgent(api_key=perplexity_api_key, model=perplexity_model)
        self._quant = QuantAgent()
        self._forecast = ForecastAgent(api_key=anthropic_api_key, model=claude_model)
        self._debate = DebateAgent(api_key=anthropic_api_key, model=claude_model)

    async def run(
        self,
        market_data: MarketData,
        context: str = "",
        quick: bool = False,
        forecast: bool = False,
        price_series: list[float] | None = None,
        vix_series: list[float] | None = None,
    ) -> EcoResult:
        if quick:
            return await self._run_quick(market_data, context)
        elif forecast:
            return await self._run_forecast(market_data, context, price_series, vix_series)
        else:
            return await self._run_full(market_data, context, price_series, vix_series)

    async def _run_quick(self, market_data: MarketData, context: str) -> EcoResult:
        """quick: AnalysisAgent만."""
        logger.info("[Orchestrator] quick 모드 — 1개 에이전트")
        signal = await self._analysis.run(market_data, context)
        consensus = ConsensusService.compute([signal])
        return EcoResult(
            consensus=consensus,
            agent_signals=[signal],
            market_data=market_data,
        )

    async def _run_full(
        self,
        market_data: MarketData,
        context: str,
        price_series: list[float] | None = None,
        vix_series: list[float] | None = None,
    ) -> EcoResult:
        """full: Analysis + Research + Quant (병렬) → Debate (순차)."""
        logger.info("[Orchestrator] full 모드 — 3개 에이전트 병렬 + Debate 순차")

        # Phase 1: 병렬 실행
        raw_results = await asyncio.gather(
            self._analysis.run(market_data, context),
            self._research.run(market_data, context),
            self._quant.execute(market_data, context, price_series, vix_series),
            return_exceptions=True,
        )

        valid: list[EconomicSignal] = []
        for r in raw_results:
            if isinstance(r, EconomicSignal):
                valid.append(r)
            else:
                logger.warning(f"[Orchestrator] 에이전트 실패: {r}")

        # Phase 2: Debate (순차 — 다른 에이전트 결과 필요)
        debate_summary = ""
        if valid:
            signals_text = self._format_signals_for_debate(valid)
            try:
                debate_signal = await self._debate.run(market_data, signals_text)
                valid.append(debate_signal)
                debate_summary = debate_signal.rationale
            except Exception as e:
                logger.warning(f"[Orchestrator] Debate 실패: {e}")

        consensus = ConsensusService.compute(valid)

        regime = self._quant.regime
        risk_metrics = self._quant.risk_metrics

        logger.info(
            f"[Orchestrator] 합의: {consensus.signal.value} "
            f"(conf={consensus.confidence:.0%})"
        )

        return EcoResult(
            consensus=consensus,
            agent_signals=valid,
            market_data=market_data,
            regime=regime,
            risk_metrics=risk_metrics,
            debate_summary=debate_summary,
        )

    async def _run_forecast(
        self,
        market_data: MarketData,
        context: str,
        price_series: list[float] | None = None,
        vix_series: list[float] | None = None,
    ) -> EcoResult:
        """forecast: full + ForecastAgent."""
        logger.info("[Orchestrator] forecast 모드 — 4개 에이전트 + Debate")

        # Phase 1: 병렬 (4개)
        raw_results = await asyncio.gather(
            self._analysis.run(market_data, context),
            self._research.run(market_data, context),
            self._quant.execute(market_data, context, price_series, vix_series),
            self._forecast.run(market_data, context),
            return_exceptions=True,
        )

        valid: list[EconomicSignal] = []
        for r in raw_results:
            if isinstance(r, EconomicSignal):
                valid.append(r)
            else:
                logger.warning(f"[Orchestrator] 에이전트 실패: {r}")

        # Phase 2: Debate
        debate_summary = ""
        if valid:
            signals_text = self._format_signals_for_debate(valid)
            try:
                debate_signal = await self._debate.run(market_data, signals_text)
                valid.append(debate_signal)
                debate_summary = debate_signal.rationale
            except Exception as e:
                logger.warning(f"[Orchestrator] Debate 실패: {e}")

        consensus = ConsensusService.compute(valid)

        return EcoResult(
            consensus=consensus,
            agent_signals=valid,
            market_data=market_data,
            regime=self._quant.regime,
            risk_metrics=self._quant.risk_metrics,
            debate_summary=debate_summary,
        )

    @staticmethod
    def _format_signals_for_debate(signals: list[EconomicSignal]) -> str:
        """에이전트 신호를 Debate 프롬프트용 텍스트로 포맷."""
        lines = []
        for s in signals:
            lines.append(
                f"- {s.agent}: {s.signal.value} (신뢰도 {s.confidence:.0%}) "
                f"— {s.rationale[:200]}"
            )
        return "\n".join(lines)
