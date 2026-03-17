"""
domain/forecast.py — HorizonType enum + ForecastResult Value Object

규칙: 이 파일은 stdlib 외 import 금지 (anthropic, httpx, yfinance 등 절대 금지).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .signal import Signal


class HorizonType(str, Enum):
    """전망 시계"""
    SHORT_TERM = "short_term"       # ≤30일
    MEDIUM_TERM = "medium_term"     # 31-90일
    LONG_TERM = "long_term"         # ≥180일


@dataclass(frozen=True)
class ForecastResult:
    """
    전망 결과 — Value Object (불변).

    horizon: 전망 시계
    signal: 전망 방향
    confidence: 0.0 ~ 1.0
    rationale: 전망 근거
    key_drivers: 주요 동인 (자연어)
    risks: 리스크 요인 (자연어)
    timestamp: ISO 8601
    """

    horizon: HorizonType
    signal: Signal
    confidence: float
    rationale: str
    key_drivers: str = ""
    risks: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0~1, got {self.confidence}")
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "horizon": self.horizon.value,
            "signal": self.signal.value,
            "confidence": round(self.confidence, 4),
            "rationale": self.rationale,
            "key_drivers": self.key_drivers,
            "risks": self.risks,
            "timestamp": self.timestamp,
        }
