"""
agents/quant.py — QuantAgent (순수 정량 분석, LLM 호출 없음)

레짐 탐지 + 리스크 계산 + LASSO 예측 → 정량 기반 EconomicSignal 반환.
결정적(deterministic) — 같은 데이터면 같은 결과.

모든 임계값은 domain/thresholds.py에서 근거와 함께 관리.
"""

from __future__ import annotations

import logging

from agents.base import BaseAgent
from domain.forecast import LASSOForecast
from domain.market_data import MarketData
from domain.regime import RegimeResult
from domain.risk import RiskLevel, RiskMetrics
from domain.signal import EconomicSignal, Signal
from domain.thresholds import (
    VIX_LOW, VIX_MID, VIX_HIGH,
    SCORE_VIX_LOW, SCORE_VIX_HIGH, SCORE_VIX_EXTREME,
    SPX_RETURN_THRESHOLD, SCORE_SPX_POSITIVE, SCORE_SPX_NEGATIVE,
    SPREAD_INVERSION, SPREAD_NEAR_INVERSION, SPREAD_NORMAL,
    SCORE_SPREAD_INVERTED, SCORE_SPREAD_NEAR, SCORE_SPREAD_NORMAL,
    DXY_STRONG, DXY_WEAK, SCORE_DXY_STRONG, SCORE_DXY_WEAK,
    RSI_OVERBOUGHT, RSI_OVERSOLD, SCORE_RSI,
    OIL_HIGH, OIL_LOW, SCORE_OIL_HIGH, SCORE_OIL_LOW,
    COPPER_HIGH, COPPER_LOW, SCORE_COPPER_HIGH, SCORE_COPPER_LOW,
    HYG_STRESS, HYG_STABLE, SCORE_HYG_STRESS, SCORE_HYG_STABLE,
    LASSO_MIN_R2, LASSO_MAX_WEIGHT,
    SIGNAL_THRESHOLD, CONFIDENCE_BASE, CONFIDENCE_CAP, CONFIDENCE_SCALE,
    SCORE_CLAMP,
)
from infrastructure.analysis import detect_regime, calculate_risk, forecast_with_lasso

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
        self._lasso: LASSOForecast | None = None

    @property
    def regime(self) -> RegimeResult | None:
        """마지막 실행의 레짐 결과 (Orchestrator에서 접근)."""
        return self._regime

    @property
    def risk_metrics(self) -> RiskMetrics | None:
        """마지막 실행의 리스크 결과 (Orchestrator에서 접근)."""
        return self._risk

    @property
    def lasso_forecast(self) -> LASSOForecast | None:
        """마지막 실행의 LASSO 예측 결과 (Orchestrator에서 접근)."""
        return self._lasso

    async def execute(
        self,
        market_data: MarketData,
        context: str = "",
        price_series: list[float] | None = None,
        vix_series: list[float] | None = None,
    ) -> EconomicSignal:
        """
        정량 분석 실행.

        price_series/vix_series가 주어지면 레짐/리스크/LASSO 분석 포함.
        없으면 VIX 수준만으로 간단 판단.
        """
        # 레짐 탐지
        if price_series and vix_series:
            self._regime = detect_regime(price_series, vix_series)
        else:
            self._regime = None

        # 리스크 계산
        self._risk = calculate_risk(market_data, self._regime, price_series)

        # LASSO 예측 (시계열 충분할 때)
        if price_series and vix_series and len(price_series) >= 120:
            self._lasso = forecast_with_lasso(
                price_series=price_series,
                vix_series=vix_series,
                fed_rate=market_data.fed_rate,
                treasury_10y=market_data.treasury_10y,
                dxy_index=market_data.dxy_index,
            )
        else:
            self._lasso = None

        # 정량 신호 결정 (LASSO 포함)
        signal, confidence, rationale = self._quantitative_signal(
            market_data, self._regime, self._risk, self._lasso
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
        lasso: LASSOForecast | None,
    ) -> tuple[Signal, float, str]:
        """VIX + 레짐 + 리스크 + LASSO + 원자재 + 신용으로 신호 결정."""
        score = 0.0  # -2(극단 bearish) ~ +2(극단 bullish)
        reasons: list[str] = []

        # VIX 기반 (핵심 지표)
        vix = market_data.vix_current
        if vix < VIX_LOW.value:
            score += SCORE_VIX_LOW.weight
            reasons.append(f"VIX 안정({vix:.1f}<{VIX_LOW.value:.0f}) — {VIX_LOW.rationale}")
        elif vix < VIX_MID.value:
            reasons.append(f"VIX 보통({vix:.1f})")
        elif vix < VIX_HIGH.value:
            score += SCORE_VIX_HIGH.weight
            reasons.append(f"VIX 높음({vix:.1f}≥{VIX_MID.value:.0f}) — {VIX_MID.rationale}")
        else:
            score += SCORE_VIX_EXTREME.weight
            reasons.append(f"VIX 극단({vix:.1f}≥{VIX_HIGH.value:.0f}) — {VIX_HIGH.rationale}")

        # SPX 30일 수익률
        spx_ret = market_data.spx_return_30d
        thr = SPX_RETURN_THRESHOLD.value
        if spx_ret > thr:
            score += SCORE_SPX_POSITIVE.weight
            reasons.append(f"SPX 30d +{spx_ret:.1f}%(>{thr:.0f}%) — {SCORE_SPX_POSITIVE.rationale}")
        elif spx_ret < -thr:
            score += SCORE_SPX_NEGATIVE.weight
            reasons.append(f"SPX 30d {spx_ret:.1f}%(<-{thr:.0f}%) — {SCORE_SPX_NEGATIVE.rationale}")

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
            reasons.append(f"레짐={regime.regime.value}(기여={rs:+.2f})")

        # 리스크 레벨
        risk_adj = {
            RiskLevel.LOW: 0.1,
            RiskLevel.MEDIUM: 0.0,
            RiskLevel.HIGH: -0.15,
            RiskLevel.EXTREME: -0.3,
        }
        r_adj = risk_adj.get(risk.risk_level, 0.0)
        score += r_adj
        if r_adj != 0:
            reasons.append(f"리스크 {risk.risk_level.value}(기여={r_adj:+.2f})")

        # GMM 확률 반영 (있으면)
        if regime and regime.gmm_probabilities:
            gmm = dict(regime.gmm_probabilities)
            bull_p = gmm.get("Bull", 0.33)
            bear_p = gmm.get("Bear", 0.33)
            gmm_tilt = (bull_p - bear_p) * 0.3
            score += gmm_tilt
            reasons.append(f"GMM Bull={bull_p:.0%}/Bear={bear_p:.0%}(기여={gmm_tilt:+.2f})")

        # 수익률 곡선 스프레드
        spread_10y_2y = market_data.yield_spread_10y_2y
        spread_10y_ffr = market_data.yield_spread_10y_ffr
        spread = spread_10y_2y if spread_10y_2y != 0 else spread_10y_ffr
        spread_label = "10Y-2Y" if spread_10y_2y != 0 else "10Y-FFR"
        if spread != 0:
            if spread < SPREAD_INVERSION.value:
                score += SCORE_SPREAD_INVERTED.weight
                reasons.append(
                    f"{spread_label}역전({spread:+.2f}%<{SPREAD_INVERSION.value}%) "
                    f"— {SPREAD_INVERSION.rationale}"
                )
            elif spread < SPREAD_NEAR_INVERSION.value:
                score += SCORE_SPREAD_NEAR.weight
                reasons.append(f"{spread_label}근접역전({spread:+.2f}%) — {SPREAD_NEAR_INVERSION.rationale}")
            elif spread > SPREAD_NORMAL.value:
                score += SCORE_SPREAD_NORMAL.weight
                reasons.append(f"{spread_label}정상({spread:+.2f}%) — {SPREAD_NORMAL.rationale}")

        # DXY (달러 인덱스)
        dxy = market_data.dxy_index
        if dxy > DXY_STRONG.value:
            score += SCORE_DXY_STRONG.weight
            reasons.append(f"달러강세(DXY {dxy:.0f}>{DXY_STRONG.value:.0f}) — {DXY_STRONG.rationale}")
        elif dxy and dxy < DXY_WEAK.value:
            score += SCORE_DXY_WEAK.weight
            reasons.append(f"달러약세(DXY {dxy:.0f}<{DXY_WEAK.value:.0f}) — {DXY_WEAK.rationale}")

        # RSI 기반
        if regime and regime.indicators:
            ind = dict(regime.indicators)
            rsi = ind.get("rsi", 50)
            if rsi > RSI_OVERBOUGHT.value:
                score -= SCORE_RSI.weight
                reasons.append(f"RSI 과매수({rsi:.0f}>{RSI_OVERBOUGHT.value:.0f}) — {RSI_OVERBOUGHT.rationale}")
            elif rsi < RSI_OVERSOLD.value:
                score += SCORE_RSI.weight
                reasons.append(f"RSI 과매도({rsi:.0f}<{RSI_OVERSOLD.value:.0f}) — {RSI_OVERSOLD.rationale}")

        # 원유 (WTI)
        oil = market_data.oil_price
        if oil > OIL_HIGH.value:
            score += SCORE_OIL_HIGH.weight
            reasons.append(f"고유가(${oil:.0f}>${OIL_HIGH.value:.0f}) — {OIL_HIGH.rationale}")
        elif oil and oil < OIL_LOW.value:
            score += SCORE_OIL_LOW.weight
            reasons.append(f"저유가(${oil:.0f}<${OIL_LOW.value:.0f}) — {OIL_LOW.rationale}")

        # 구리 (Dr. Copper)
        copper = market_data.copper_price
        if copper > COPPER_HIGH.value:
            score += SCORE_COPPER_HIGH.weight
            reasons.append(f"구리강세(${copper:.2f}>${COPPER_HIGH.value}) — {COPPER_HIGH.rationale}")
        elif copper and copper < COPPER_LOW.value:
            score += SCORE_COPPER_LOW.weight
            reasons.append(f"구리약세(${copper:.2f}<${COPPER_LOW.value}) — {COPPER_LOW.rationale}")

        # HYG (하이일드 채권 ETF)
        hyg = market_data.hyg_price
        if hyg and hyg < HYG_STRESS.value:
            score += SCORE_HYG_STRESS.weight
            reasons.append(f"신용스트레스(HYG ${hyg:.1f}<${HYG_STRESS.value:.0f}) — {HYG_STRESS.rationale}")
        elif hyg and hyg > HYG_STABLE.value:
            score += SCORE_HYG_STABLE.weight
            reasons.append(f"신용안정(HYG ${hyg:.1f}>${HYG_STABLE.value:.0f}) — {HYG_STABLE.rationale}")

        # LASSO 예측 반영 (R²가 일정 수준 이상일 때만)
        if lasso and lasso.r_squared >= LASSO_MIN_R2.value:
            lasso_weight = min(LASSO_MAX_WEIGHT.value, lasso.r_squared)
            if lasso.signal == Signal.BULLISH:
                score += lasso_weight
            elif lasso.signal == Signal.BEARISH:
                score -= lasso_weight
            lasso_dir = "+" if lasso.signal == Signal.BULLISH else "-" if lasso.signal == Signal.BEARISH else "0"
            if lasso.key_drivers:
                top_driver = lasso.key_drivers[0][0]
                reasons.append(
                    f"LASSO {lasso.predicted_return:+.1f}% "
                    f"(R²={lasso.r_squared:.2f}, 기여={lasso_dir}{lasso_weight:.2f}, 주동인={top_driver})"
                )
            else:
                reasons.append(
                    f"LASSO {lasso.predicted_return:+.1f}% "
                    f"(R²={lasso.r_squared:.2f}, 기여={lasso_dir}{lasso_weight:.2f})"
                )

        # 스코어 클램프 (극단 누적 방지)
        clamped = max(-SCORE_CLAMP.value, min(SCORE_CLAMP.value, score))
        if clamped != score:
            reasons.append(f"스코어 클램프 적용({score:+.2f}→{clamped:+.2f})")
            score = clamped

        # 신호 결정
        thr_sig = SIGNAL_THRESHOLD.value
        if score > thr_sig:
            signal = Signal.BULLISH
        elif score < -thr_sig:
            signal = Signal.BEARISH
        else:
            signal = Signal.NEUTRAL

        # 신뢰도 산출 (감쇠 곡선 + 상한)
        # 기존: min(1.0, 0.4 + abs(score)) → score 0.6에서 100% (과신)
        # 개선: base + scale * abs(score) / (1 + abs(score)) → 포화 곡선
        #   score=0.5 → 0.35 + 0.7*(0.5/1.5) = 0.58
        #   score=1.0 → 0.35 + 0.7*(1.0/2.0) = 0.70
        #   score=1.5 → 0.35 + 0.7*(1.5/2.5) = 0.77
        #   상한 0.92 — "매우 높은 확신이지만 모델 한계 인정"
        raw_conf = (
            CONFIDENCE_BASE.value
            + CONFIDENCE_SCALE.value * abs(score) / (1.0 + abs(score))
        )
        confidence = min(CONFIDENCE_CAP.value, raw_conf)
        rationale = "; ".join(reasons)

        return signal, round(confidence, 4), rationale
