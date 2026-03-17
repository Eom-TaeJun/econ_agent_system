"""
domain/risk.py — RiskLevel enum + RiskMetrics Value Object

규칙: 이 파일은 stdlib 외 import 금지 (anthropic, httpx, yfinance 등 절대 금지).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """리스크 수준"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass(frozen=True)
class RiskMetrics:
    """
    리스크 지표 — Value Object (불변).

    risk_level: 종합 리스크 수준
    vix_current: 현재 VIX
    realized_vol_20d: 20일 실현 변동성 (연환산 %)
    var_95: 95% VaR (일간 %)
    cvar_95: 95% CVaR (일간 %)
    max_drawdown: 최대 낙폭 (%)
    description: 리스크 해석
    timestamp: ISO 8601
    """

    risk_level: RiskLevel
    vix_current: float = 0.0
    realized_vol_20d: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0
    max_drawdown: float = 0.0
    description: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "risk_level": self.risk_level.value,
            "vix_current": round(self.vix_current, 2),
            "realized_vol_20d": round(self.realized_vol_20d, 2),
            "var_95": round(self.var_95, 4),
            "cvar_95": round(self.cvar_95, 4),
            "max_drawdown": round(self.max_drawdown, 2),
            "description": self.description,
            "timestamp": self.timestamp,
        }
