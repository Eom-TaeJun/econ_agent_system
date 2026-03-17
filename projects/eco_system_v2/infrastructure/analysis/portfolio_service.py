"""
infrastructure/analysis/portfolio_service.py

레짐 + 신호 + 리스크 + LASSO 기반 전략적 자산 배분 추천.
eimas lib/portfolio_optimizer.py의 HRP 아이디어(역분산 배분)를 매크로 자산 배분에 적용.

방법론:
  1. 레짐별 기본 배분 (Base Allocation)
  2. 합의 신호로 방향 조정 (Signal Tilt)
  3. 리스크 수준으로 방어도 조정 (Risk Adjustment)
  4. LASSO 예측으로 미세 조정 (Forward-Looking Tilt)
  5. 모든 조정을 투명하게 기록

참고: Lopez de Prado(2016) HRP의 역분산 배분 원리를 자산 클래스 수준에 적용

인터페이스: recommend_allocation(...) -> AllocationResult
"""

from __future__ import annotations

import logging

from domain.allocation import (
    AllocationAdjustment,
    AllocationResult,
    AssetClass,
)
from domain.forecast import LASSOForecast
from domain.regime import MarketRegime, RegimeResult
from domain.risk import RiskLevel, RiskMetrics
from domain.signal import EconomicSignal, Signal
from domain.thresholds import (
    PORTFOLIO_SIGNAL_MAX_TILT,
    PORTFOLIO_RISK_HIGH_SHIFT, PORTFOLIO_RISK_EXTREME_SHIFT, PORTFOLIO_RISK_LOW_SHIFT,
    PORTFOLIO_LASSO_MIN_R2, PORTFOLIO_LASSO_MAX_TILT,
    LASSO_BULLISH_RETURN, LASSO_BEARISH_RETURN,
)

logger = logging.getLogger(__name__)


# ============================================================================
# 레짐별 기본 배분 (Base Allocation)
# ============================================================================

_BASE_ALLOCATIONS: dict[MarketRegime, dict[AssetClass, float]] = {
    MarketRegime.BULL_LOW_VOL: {
        AssetClass.EQUITY: 70,
        AssetClass.BOND: 15,
        AssetClass.GOLD: 10,
        AssetClass.CASH: 5,
    },
    MarketRegime.BULL_HIGH_VOL: {
        AssetClass.EQUITY: 50,
        AssetClass.BOND: 20,
        AssetClass.GOLD: 15,
        AssetClass.CASH: 15,
    },
    MarketRegime.TRANSITION: {
        AssetClass.EQUITY: 40,
        AssetClass.BOND: 25,
        AssetClass.GOLD: 15,
        AssetClass.CASH: 20,
    },
    MarketRegime.BEAR_LOW_VOL: {
        AssetClass.EQUITY: 30,
        AssetClass.BOND: 30,
        AssetClass.GOLD: 20,
        AssetClass.CASH: 20,
    },
    MarketRegime.BEAR_HIGH_VOL: {
        AssetClass.EQUITY: 10,
        AssetClass.BOND: 25,
        AssetClass.GOLD: 25,
        AssetClass.CASH: 40,
    },
}

# 레짐 없을 때 기본값 (중립)
_DEFAULT_ALLOCATION = {
    AssetClass.EQUITY: 40,
    AssetClass.BOND: 25,
    AssetClass.GOLD: 15,
    AssetClass.CASH: 20,
}

# 전략명 매핑
_STRATEGY_NAMES: dict[MarketRegime, str] = {
    MarketRegime.BULL_LOW_VOL: "공격적 성장",
    MarketRegime.BULL_HIGH_VOL: "변동성 대응 성장",
    MarketRegime.TRANSITION: "균형 관망",
    MarketRegime.BEAR_LOW_VOL: "방어적 저점매수",
    MarketRegime.BEAR_HIGH_VOL: "자산 보존",
}


def recommend_allocation(
    consensus: EconomicSignal,
    regime: RegimeResult | None = None,
    risk: RiskMetrics | None = None,
    lasso: LASSOForecast | None = None,
) -> AllocationResult:
    """
    파이프라인 결과를 종합하여 자산 배분을 추천한다.

    consensus: 합의 EconomicSignal
    regime: 레짐 탐지 결과 (선택)
    risk: 리스크 지표 (선택)
    lasso: LASSO 예측 (선택)

    Returns: AllocationResult
    """
    adjustments: list[AllocationAdjustment] = []

    # 1. 레짐별 기본 배분
    if regime:
        alloc = dict(_BASE_ALLOCATIONS.get(regime.regime, _DEFAULT_ALLOCATION))
        strategy = _STRATEGY_NAMES.get(regime.regime, "균형")
    else:
        alloc = dict(_DEFAULT_ALLOCATION)
        strategy = "균형 (레짐 미확인)"

    # 2. 합의 신호 조정
    _apply_signal_tilt(alloc, consensus, adjustments)

    # 3. 리스크 수준 조정
    if risk:
        _apply_risk_adjustment(alloc, risk, adjustments)

    # 4. LASSO 예측 조정
    if lasso and lasso.r_squared >= PORTFOLIO_LASSO_MIN_R2.value:
        _apply_lasso_tilt(alloc, lasso, adjustments)

    # 5. 정규화 (합계 100%)
    _normalize(alloc)

    # 6. 설명 생성
    rationale = _build_rationale(alloc, strategy, regime, consensus, risk, lasso, adjustments)

    allocations_tuple = tuple(
        (ac.value, round(alloc[ac], 2))
        for ac in AssetClass
    )

    logger.info(
        f"[portfolio] {strategy}: "
        + ", ".join(f"{ac.value}={alloc[ac]:.0f}%" for ac in AssetClass)
    )

    return AllocationResult(
        allocations=allocations_tuple,
        strategy_name=strategy,
        adjustments=tuple(adjustments),
        rationale=rationale,
    )


# ============================================================================
# 조정 함수
# ============================================================================

def _apply_signal_tilt(
    alloc: dict[AssetClass, float],
    consensus: EconomicSignal,
    adjustments: list[AllocationAdjustment],
) -> None:
    """합의 신호에 따른 배분 조정."""
    signal = consensus.signal
    conf = consensus.confidence

    max_tilt = PORTFOLIO_SIGNAL_MAX_TILT.value
    strength = conf * max_tilt

    if signal == Signal.BULLISH:
        eq_add = min(strength, max_tilt)
        alloc[AssetClass.EQUITY] += eq_add
        alloc[AssetClass.CASH] -= eq_add * 0.5
        alloc[AssetClass.BOND] -= eq_add * 0.5
        adjustments.append(AllocationAdjustment(
            source="signal",
            asset=AssetClass.EQUITY,
            delta=eq_add,
            reason=f"BULLISH 합의 (신뢰도 {conf:.0%}) → 주식 비중 확대",
        ))

    elif signal == Signal.BEARISH:
        eq_cut = min(strength, max_tilt)
        alloc[AssetClass.EQUITY] -= eq_cut
        alloc[AssetClass.GOLD] += eq_cut * 0.4
        alloc[AssetClass.CASH] += eq_cut * 0.6
        adjustments.append(AllocationAdjustment(
            source="signal",
            asset=AssetClass.EQUITY,
            delta=-eq_cut,
            reason=f"BEARISH 합의 (신뢰도 {conf:.0%}) → 주식 비중 축소, 안전자산 확대",
        ))


def _apply_risk_adjustment(
    alloc: dict[AssetClass, float],
    risk: RiskMetrics,
    adjustments: list[AllocationAdjustment],
) -> None:
    """리스크 수준에 따른 방어도 조정."""
    if risk.risk_level == RiskLevel.HIGH:
        shift = PORTFOLIO_RISK_HIGH_SHIFT.value
        alloc[AssetClass.EQUITY] -= shift
        alloc[AssetClass.CASH] += shift
        adjustments.append(AllocationAdjustment(
            source="risk",
            asset=AssetClass.CASH,
            delta=shift,
            reason=f"리스크 HIGH (VIX {risk.vix_current:.1f}) → 현금 비중 확대",
        ))

    elif risk.risk_level == RiskLevel.EXTREME:
        shift = PORTFOLIO_RISK_EXTREME_SHIFT.value
        alloc[AssetClass.EQUITY] -= shift
        alloc[AssetClass.GOLD] += shift * 0.4
        alloc[AssetClass.CASH] += shift * 0.6
        adjustments.append(AllocationAdjustment(
            source="risk",
            asset=AssetClass.EQUITY,
            delta=-shift,
            reason=f"리스크 EXTREME (VIX {risk.vix_current:.1f}) → 위험자산 대폭 축소",
        ))

    elif risk.risk_level == RiskLevel.LOW:
        shift = PORTFOLIO_RISK_LOW_SHIFT.value
        alloc[AssetClass.EQUITY] += shift
        alloc[AssetClass.CASH] -= shift
        adjustments.append(AllocationAdjustment(
            source="risk",
            asset=AssetClass.EQUITY,
            delta=shift,
            reason=f"리스크 LOW (VIX {risk.vix_current:.1f}) → 위험자산 소폭 확대",
        ))


def _apply_lasso_tilt(
    alloc: dict[AssetClass, float],
    lasso: LASSOForecast,
    adjustments: list[AllocationAdjustment],
) -> None:
    """LASSO 예측에 따른 미세 조정."""
    pred = lasso.predicted_return
    r2 = lasso.r_squared

    max_tilt = PORTFOLIO_LASSO_MAX_TILT.value
    strength = min(max_tilt, abs(pred) * r2 * 2)

    if pred > LASSO_BULLISH_RETURN.value:
        alloc[AssetClass.EQUITY] += strength
        alloc[AssetClass.CASH] -= strength
        adjustments.append(AllocationAdjustment(
            source="lasso",
            asset=AssetClass.EQUITY,
            delta=strength,
            reason=f"LASSO +{pred:.1f}% 전망 (R²={r2:.2f}) → 주식 소폭 추가",
        ))
    elif pred < LASSO_BEARISH_RETURN.value:
        alloc[AssetClass.EQUITY] -= strength
        alloc[AssetClass.GOLD] += strength * 0.5
        alloc[AssetClass.CASH] += strength * 0.5
        adjustments.append(AllocationAdjustment(
            source="lasso",
            asset=AssetClass.EQUITY,
            delta=-strength,
            reason=f"LASSO {pred:.1f}% 전망 (R²={r2:.2f}) → 주식 소폭 축소",
        ))


# ============================================================================
# 정규화 + 설명
# ============================================================================

def _normalize(alloc: dict[AssetClass, float]) -> None:
    """합계를 100%로 정규화하고, 음수를 0으로 클램프."""
    for ac in AssetClass:
        alloc[ac] = max(0, alloc[ac])

    total = sum(alloc.values())
    if total > 0:
        for ac in AssetClass:
            alloc[ac] = alloc[ac] / total * 100


def _build_rationale(
    alloc: dict[AssetClass, float],
    strategy: str,
    regime: RegimeResult | None,
    consensus: EconomicSignal,
    risk: RiskMetrics | None,
    lasso: LASSOForecast | None,
    adjustments: list[AllocationAdjustment],
) -> str:
    """사람이 읽는 배분 근거 설명."""
    lines: list[str] = []

    # 전략 요약
    regime_str = regime.regime.value if regime else "미확인"
    lines.append(f"전략: {strategy} (레짐: {regime_str})")

    # 배분 결과
    alloc_str = " | ".join(f"{ac.value} {alloc[ac]:.0f}%" for ac in AssetClass)
    lines.append(f"배분: {alloc_str}")

    # 조정 이력
    if adjustments:
        lines.append("조정 이력:")
        for adj in adjustments:
            lines.append(f"  [{adj.source}] {adj.reason}")

    # 핵심 판단 요약
    risk_str = f", 리스크 {risk.risk_level.value}" if risk else ""
    lasso_str = f", LASSO {lasso.predicted_return:+.1f}%" if lasso and lasso.r_squared >= PORTFOLIO_LASSO_MIN_R2.value else ""
    lines.append(
        f"근거: {consensus.signal.value} 합의({consensus.confidence:.0%})"
        f"{risk_str}{lasso_str}"
    )

    return "\n".join(lines)
