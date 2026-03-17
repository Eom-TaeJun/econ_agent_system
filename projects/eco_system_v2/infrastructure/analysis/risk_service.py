"""
infrastructure/analysis/risk_service.py

VIX + 실현변동성 + 가격 시리즈 기반 리스크 지표 계산.
eimas lib/risk_manager.py에서 핵심 알고리즘만 추출.

인터페이스: calculate_risk(market_data, regime) -> RiskMetrics
"""

from __future__ import annotations

import logging
import math

from domain.market_data import MarketData
from domain.regime import MarketRegime, RegimeResult
from domain.risk import RiskLevel, RiskMetrics

logger = logging.getLogger(__name__)


def calculate_risk(
    market_data: MarketData,
    regime: RegimeResult | None = None,
    price_series: list[float] | None = None,
) -> RiskMetrics:
    """
    시장 데이터와 레짐 정보로 리스크 지표를 계산한다.

    market_data: 현재 거시경제 스냅샷
    regime: 레짐 탐지 결과 (선택)
    price_series: 일봉 종가 시리즈 (VaR/MDD 계산용, 선택)

    Returns: RiskMetrics (domain VO)
    """
    vix = market_data.vix_current

    # 수익률 곡선 스프레드 (10Y - FFR)
    yield_spread = 0.0
    if market_data.treasury_10y and market_data.fed_rate:
        yield_spread = market_data.treasury_10y - market_data.fed_rate

    # 리스크 수준 분류 (수익률 곡선 반영)
    risk_level = _classify_risk_level(vix, regime, yield_spread)

    # 실현 변동성 계산 (가격 시리즈 있을 때)
    realized_vol = 0.0
    var_95 = 0.0
    cvar_95 = 0.0
    max_drawdown = 0.0

    if price_series and len(price_series) >= 20:
        returns = _daily_returns(price_series)
        realized_vol = _realized_volatility(returns, window=20)
        var_95 = _historical_var(returns, confidence=0.95)
        cvar_95 = _historical_cvar(returns, confidence=0.95)
        max_drawdown = _max_drawdown(price_series)

    description = _build_description(risk_level, vix, regime, yield_spread)

    logger.info(
        f"[risk] level={risk_level.value}, VIX={vix:.1f}, "
        f"realized_vol={realized_vol:.1f}%, MDD={max_drawdown:.1f}%, "
        f"yield_spread={yield_spread:+.2f}%"
    )

    return RiskMetrics(
        risk_level=risk_level,
        vix_current=vix,
        realized_vol_20d=realized_vol,
        var_95=var_95,
        cvar_95=cvar_95,
        max_drawdown=max_drawdown,
        description=description,
    )


def _classify_risk_level(
    vix: float,
    regime: RegimeResult | None,
    yield_spread: float = 0.0,
) -> RiskLevel:
    """VIX + 레짐 + 수익률 곡선 스프레드로 리스크 수준 분류."""
    if vix >= 30.0:
        return RiskLevel.EXTREME
    if vix >= 22.0:
        # 수익률 곡선 역전(10Y < FFR) → 경기침체 경고 → EXTREME
        if yield_spread < -0.5:
            return RiskLevel.EXTREME
        return RiskLevel.HIGH

    # 레짐이 Bear이면 한 단계 올림
    if regime and regime.regime in (
        MarketRegime.BEAR_LOW_VOL,
        MarketRegime.BEAR_HIGH_VOL,
    ):
        if vix >= 16.0:
            return RiskLevel.HIGH
        return RiskLevel.MEDIUM

    # 수익률 곡선 역전 단독 → 최소 MEDIUM
    if yield_spread < -0.5:
        return RiskLevel.MEDIUM

    if vix >= 16.0:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _daily_returns(prices: list[float]) -> list[float]:
    """일간 수익률 계산."""
    return [
        (prices[i] / prices[i - 1]) - 1.0
        for i in range(1, len(prices))
        if prices[i - 1] != 0
    ]


def _realized_volatility(returns: list[float], window: int = 20) -> float:
    """실현 변동성 (연환산 %)."""
    if len(returns) < window:
        return 0.0

    recent = returns[-window:]
    mean = sum(recent) / len(recent)
    variance = sum((r - mean) ** 2 for r in recent) / (len(recent) - 1)
    daily_vol = math.sqrt(variance)
    annual_vol = daily_vol * math.sqrt(252) * 100
    return round(annual_vol, 2)


def _historical_var(returns: list[float], confidence: float = 0.95) -> float:
    """Historical VaR (일간 %)."""
    if not returns:
        return 0.0
    sorted_returns = sorted(returns)
    index = int((1 - confidence) * len(sorted_returns))
    return round(sorted_returns[index] * 100, 4)


def _historical_cvar(returns: list[float], confidence: float = 0.95) -> float:
    """Historical CVaR / Expected Shortfall (일간 %)."""
    if not returns:
        return 0.0
    sorted_returns = sorted(returns)
    cutoff = int((1 - confidence) * len(sorted_returns))
    if cutoff == 0:
        return round(sorted_returns[0] * 100, 4)
    tail = sorted_returns[:cutoff]
    return round((sum(tail) / len(tail)) * 100, 4)


def _max_drawdown(prices: list[float]) -> float:
    """최대 낙폭 (%)."""
    if len(prices) < 2:
        return 0.0

    peak = prices[0]
    max_dd = 0.0
    for price in prices:
        if price > peak:
            peak = price
        dd = (peak - price) / peak * 100 if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)


def _build_description(
    risk_level: RiskLevel,
    vix: float,
    regime: RegimeResult | None,
    yield_spread: float = 0.0,
) -> str:
    """리스크 상태 해석 문장."""
    regime_str = regime.regime.value if regime else "Unknown"
    spread_str = ""
    if yield_spread != 0:
        if yield_spread < -0.5:
            spread_str = f" 수익률 곡선 역전({yield_spread:+.2f}%) — 경기침체 경고."
        elif yield_spread < 0:
            spread_str = f" 수익률 곡선 근접 역전({yield_spread:+.2f}%)."
        else:
            spread_str = f" 수익률 곡선 정상({yield_spread:+.2f}%)."

    descriptions = {
        RiskLevel.LOW: f"리스크 낮음 (VIX {vix:.1f}). {regime_str} 레짐에서 안정적 환경.{spread_str}",
        RiskLevel.MEDIUM: f"리스크 보통 (VIX {vix:.1f}). 주의 관찰 필요.{spread_str}",
        RiskLevel.HIGH: f"리스크 높음 (VIX {vix:.1f}). 방어적 포지셔닝 권장.{spread_str}",
        RiskLevel.EXTREME: f"리스크 극단 (VIX {vix:.1f}). 자산 보존 최우선.{spread_str}",
    }
    return descriptions.get(risk_level, f"VIX {vix:.1f}")
