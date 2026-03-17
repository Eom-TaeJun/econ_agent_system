"""
agents/quant.py — QuantAgent (순수 정량 분석, LLM 호출 없음)

레짐 탐지 + 리스크 계산 → 정량 기반 EconomicSignal 반환.
결정적(deterministic) — 같은 데이터면 같은 결과.
"""

from __future__ import annotations

import logging

from agents.base import BaseAgent
from domain.market_data import MarketData
from domain.regime import RegimeResult
from domain.risk import RiskLevel, RiskMetrics
from domain.signal import EconomicSignal, Signal
from infrastructure.analysis import detect_regime, calculate_risk

logger = logging.getLogger(__name__)


class QuantAgent(BaseAgent):
    """
    정량 분석 에이전트 — LLM 없이 순수 계산.

    ADR: 객관적 정량 신호와 주관적 LLM 해석을 분리.
    빠르고, 저렴하고, 결정적(deterministic).
    """

    def __init__(self) -> None:
        super().__init__("quant", max_retries=1, timeout_sec=30.0)
        self._regime: RegimeResult | None = None
        self._risk: RiskMetrics | None = None

    @property
    def regime(self) -> RegimeResult | None:
        """마지막 실행의 레짐 결과 (Orchestrator에서 접근)."""
        return self._regime

    @property
    def risk_metrics(self) -> RiskMetrics | None:
        """마지막 실행의 리스크 결과 (Orchestrator에서 접근)."""
        return self._risk

    async def execute(
        self,
        market_data: MarketData,
        context: str = "",
        price_series: list[float] | None = None,
        vix_series: list[float] | None = None,
    ) -> EconomicSignal:
        """
        정량 분석 실행.

        price_series/vix_series가 주어지면 레짐/리스크 분석 포함.
        없으면 VIX 수준만으로 간단 판단.
        """
        # 레짐 탐지
        if price_series and vix_series:
            self._regime = detect_regime(price_series, vix_series)
        else:
            self._regime = None

        # 리스크 계산
        self._risk = calculate_risk(market_data, self._regime, price_series)

        # 정량 신호 결정
        signal, confidence, rationale = self._quantitative_signal(
            market_data, self._regime, self._risk
        )

        logger.info(f"[quant] signal={signal.value} conf={confidence:.2f}")

        return EconomicSignal(
            agent=self.name,
            signal=signal,
            confidence=confidence,
            rationale=rationale,
        )

    def _quantitative_signal(
        self,
        market_data: MarketData,
        regime: RegimeResult | None,
        risk: RiskMetrics,
    ) -> tuple[Signal, float, str]:
        """VIX + 레짐 + 리스크로 신호 결정."""
        score = 0.0  # -1(bearish) ~ +1(bullish)
        reasons: list[str] = []

        # VIX 기반 (기본)
        vix = market_data.vix_current
        if vix < 16:
            score += 0.3
            reasons.append(f"VIX 안정({vix:.1f})")
        elif vix < 22:
            reasons.append(f"VIX 보통({vix:.1f})")
        elif vix < 30:
            score -= 0.3
            reasons.append(f"VIX 높음({vix:.1f})")
        else:
            score -= 0.5
            reasons.append(f"VIX 극단({vix:.1f})")

        # SPX 30일 수익률
        spx_ret = market_data.spx_return_30d
        if spx_ret > 3:
            score += 0.2
            reasons.append(f"SPX 30d +{spx_ret:.1f}%")
        elif spx_ret < -3:
            score -= 0.2
            reasons.append(f"SPX 30d {spx_ret:.1f}%")

        # 레짐 기반
        if regime:
            from domain.regime import MarketRegime
            regime_scores = {
                MarketRegime.BULL_LOW_VOL: 0.3,
                MarketRegime.BULL_HIGH_VOL: 0.1,
                MarketRegime.TRANSITION: 0.0,
                MarketRegime.BEAR_LOW_VOL: -0.15,
                MarketRegime.BEAR_HIGH_VOL: -0.35,
            }
            rs = regime_scores.get(regime.regime, 0.0)
            score += rs
            reasons.append(f"레짐={regime.regime.value}")

        # 리스크 레벨
        risk_adj = {
            RiskLevel.LOW: 0.1,
            RiskLevel.MEDIUM: 0.0,
            RiskLevel.HIGH: -0.15,
            RiskLevel.EXTREME: -0.3,
        }
        score += risk_adj.get(risk.risk_level, 0.0)

        # GMM 확률 반영 (있으면)
        if regime and regime.gmm_probabilities:
            gmm = dict(regime.gmm_probabilities)
            bull_p = gmm.get("Bull", 0.33)
            bear_p = gmm.get("Bear", 0.33)
            gmm_tilt = (bull_p - bear_p) * 0.3  # GMM net 방향 반영
            score += gmm_tilt
            reasons.append(f"GMM Bull={bull_p:.0%}/Bear={bear_p:.0%}")

        # 수익률 곡선 스프레드 (10Y - FFR)
        if market_data.treasury_10y and market_data.fed_rate:
            spread = market_data.treasury_10y - market_data.fed_rate
            if spread < -0.5:
                score -= 0.25
                reasons.append(f"곡선역전({spread:+.2f}%)")
            elif spread < 0:
                score -= 0.1
                reasons.append(f"곡선근접역전({spread:+.2f}%)")
            elif spread > 1.0:
                score += 0.1
                reasons.append(f"곡선정상({spread:+.2f}%)")

        # DXY (달러 강세 = 위험자산 약세)
        dxy = market_data.dxy_index
        if dxy > 105:
            score -= 0.1
            reasons.append(f"달러강세(DXY {dxy:.0f})")
        elif dxy and dxy < 95:
            score += 0.1
            reasons.append(f"달러약세(DXY {dxy:.0f})")

        # RSI 기반 (regime indicators에서)
        if regime and regime.indicators:
            ind = dict(regime.indicators)
            rsi = ind.get("rsi", 50)
            if rsi > 70:
                score -= 0.05
                reasons.append(f"RSI 과매수({rsi:.0f})")
            elif rsi < 30:
                score += 0.05
                reasons.append(f"RSI 과매도({rsi:.0f})")

        # 신호 결정
        if score > 0.2:
            signal = Signal.BULLISH
        elif score < -0.2:
            signal = Signal.BEARISH
        else:
            signal = Signal.NEUTRAL

        confidence = min(1.0, 0.4 + abs(score))
        rationale = "; ".join(reasons)

        return signal, round(confidence, 4), rationale
