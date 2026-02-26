"""
domain/signal.py — Signal enum + EconomicSignal Value Object

규칙: 이 파일은 stdlib 외 import 금지 (anthropic, httpx, yfinance 등 절대 금지).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Signal(str, Enum):
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"


@dataclass(frozen=True)
class EconomicSignal:
    """
    에이전트 1개의 판단 결과 — Value Object (불변).

    agent: 판단한 에이전트 이름
    signal: BULLISH / NEUTRAL / BEARISH
    confidence: 0.0 ~ 1.0
    rationale: 판단 근거 (자연어)
    timestamp: ISO 8601 문자열
    """

    agent: str
    signal: Signal
    confidence: float
    rationale: str
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0~1, got {self.confidence}")
        if not self.timestamp:
            # frozen=True이므로 object.__setattr__ 사용
            object.__setattr__(self, "timestamp", datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "signal": self.signal.value,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "timestamp": self.timestamp,
        }
