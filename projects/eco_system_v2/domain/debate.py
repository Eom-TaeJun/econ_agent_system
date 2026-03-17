"""
domain/debate.py — DebateResult Value Object

규칙: 이 파일은 stdlib 외 import 금지 (anthropic, httpx, yfinance 등 절대 금지).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .signal import Signal


@dataclass(frozen=True)
class DebateResult:
    """
    토론 합의 결과 — Value Object (불변).

    다른 에이전트 신호를 종합한 뒤 DebateAgent가 합의에 도전한 결과.

    final_signal: 토론 후 최종 판단
    confidence: 0.0 ~ 1.0
    agreement_ratio: 원래 합의와 얼마나 동의하는지 (0.0 ~ 1.0)
    challenges: 합의에 대한 도전/반론
    synthesis: 종합 해석
    timestamp: ISO 8601
    """

    final_signal: Signal
    confidence: float
    agreement_ratio: float
    challenges: str
    synthesis: str
    agent_signals_summary: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0~1, got {self.confidence}")
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "final_signal": self.final_signal.value,
            "confidence": round(self.confidence, 4),
            "agreement_ratio": round(self.agreement_ratio, 4),
            "challenges": self.challenges,
            "synthesis": self.synthesis,
            "agent_signals_summary": self.agent_signals_summary,
            "timestamp": self.timestamp,
        }
