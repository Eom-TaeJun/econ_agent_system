"""
domain/regime.py — MarketRegime enum + RegimeResult Value Object

규칙: 이 파일은 stdlib 외 import 금지 (anthropic, httpx, yfinance 등 절대 금지).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MarketRegime(str, Enum):
    """시장 레짐 — Hamilton(1989) Markov Switching 간소화"""
    BULL_LOW_VOL = "Bull (Low Vol)"
    BULL_HIGH_VOL = "Bull (High Vol)"
    BEAR_LOW_VOL = "Bear (Low Vol)"
    BEAR_HIGH_VOL = "Bear (High Vol)"
    TRANSITION = "Transition"


class TrendState(str, Enum):
    """추세 상태"""
    STRONG_UP = "Strong Uptrend"
    WEAK_UP = "Weak Uptrend"
    NEUTRAL = "Neutral"
    WEAK_DOWN = "Weak Downtrend"
    STRONG_DOWN = "Strong Downtrend"


class VolatilityState(str, Enum):
    """변동성 상태"""
    VERY_LOW = "Very Low"
    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"
    EXTREME = "Extreme"


@dataclass(frozen=True)
class RegimeResult:
    """
    레짐 탐지 결과 — Value Object (불변).

    regime: 현재 시장 레짐
    confidence: 0.0 ~ 1.0
    trend_state: 추세 상태
    volatility_state: 변동성 상태
    description: 레짐 해석
    strategy: 권장 전략
    risk_appetite: 리스크 선호도 (HIGH/MEDIUM/LOW/VERY_LOW/NEUTRAL)
    timestamp: ISO 8601
    """

    regime: MarketRegime
    confidence: float
    trend_state: TrendState
    volatility_state: VolatilityState
    description: str
    strategy: str
    risk_appetite: str
    timestamp: str = ""
    prev_regime: str = ""
    days_in_regime: int = 0
    # GMM 확률 (Bull/Neutral/Bear)
    gmm_probabilities: tuple[tuple[str, float], ...] = ()
    # 기술적 지표
    indicators: tuple[tuple[str, float], ...] = ()
    # 전환 확률
    transition_probs: tuple[tuple[str, float], ...] = ()

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "regime": self.regime.value,
            "confidence": round(self.confidence, 4),
            "trend_state": self.trend_state.value,
            "volatility_state": self.volatility_state.value,
            "description": self.description,
            "strategy": self.strategy,
            "risk_appetite": self.risk_appetite,
            "timestamp": self.timestamp,
            "prev_regime": self.prev_regime,
            "days_in_regime": self.days_in_regime,
            "gmm_probabilities": dict(self.gmm_probabilities),
            "indicators": dict(self.indicators),
            "transition_probs": dict(self.transition_probs),
        }
