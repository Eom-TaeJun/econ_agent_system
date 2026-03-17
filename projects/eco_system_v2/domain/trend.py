"""
domain/trend.py — 트렌드 추적 Value Objects

과거 분석 결과와 현재를 비교하기 위한 도메인 모델.

규칙: 이 파일은 stdlib 외 import 금지.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .signal import Signal


class Direction(str, Enum):
    """신호 변화 방향."""
    UPGRADED = "upgraded"       # BEARISH→NEUTRAL, NEUTRAL→BULLISH 등
    DOWNGRADED = "downgraded"   # BULLISH→NEUTRAL, NEUTRAL→BEARISH 등
    REVERSED = "reversed"       # BULLISH→BEARISH, BEARISH→BULLISH
    UNCHANGED = "unchanged"


# Signal 순서 (높을수록 긍정적)
_SIGNAL_ORDER = {Signal.BEARISH: 0, Signal.NEUTRAL: 1, Signal.BULLISH: 2}


def classify_direction(prev: Signal, curr: Signal) -> Direction:
    """이전→현재 신호 변화의 방향을 분류한다."""
    if prev == curr:
        return Direction.UNCHANGED
    diff = _SIGNAL_ORDER[curr] - _SIGNAL_ORDER[prev]
    if abs(diff) == 2:
        return Direction.REVERSED
    return Direction.UPGRADED if diff > 0 else Direction.DOWNGRADED


@dataclass(frozen=True)
class SignalChange:
    """에이전트 하나의 신호 변화."""

    agent: str
    previous_signal: Signal
    current_signal: Signal
    previous_confidence: float
    current_confidence: float
    direction: Direction

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "previous": self.previous_signal.value,
            "current": self.current_signal.value,
            "prev_confidence": self.previous_confidence,
            "curr_confidence": self.current_confidence,
            "direction": self.direction.value,
        }


@dataclass(frozen=True)
class TrendSnapshot:
    """과거 분석 하나의 스냅샷."""

    date: str
    consensus_signal: Signal
    consensus_confidence: float
    agent_signals: tuple[tuple[str, str, float], ...]  # (agent, signal, confidence)

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "consensus_signal": self.consensus_signal.value,
            "consensus_confidence": self.consensus_confidence,
            "agents": [
                {"agent": a, "signal": s, "confidence": c}
                for a, s, c in self.agent_signals
            ],
        }


@dataclass(frozen=True)
class TrendComparison:
    """현재 vs 과거 비교 결과."""

    current_date: str
    previous_date: str                                  # 직전 실행 날짜 (없으면 "")
    consensus_direction: Direction                      # 합의 방향 변화
    signal_changes: tuple[SignalChange, ...]             # 에이전트별 변화
    streak: int                                         # 같은 방향 연속 횟수
    streak_signal: Signal                               # 연속 방향
    confidence_delta: float                             # 신뢰도 변화
    recent_history: tuple[TrendSnapshot, ...]            # 최근 N개 스냅샷
    explanation: str                                    # 사람이 읽는 요약

    def to_dict(self) -> dict:
        return {
            "current_date": self.current_date,
            "previous_date": self.previous_date,
            "consensus_direction": self.consensus_direction.value,
            "signal_changes": [c.to_dict() for c in self.signal_changes],
            "streak": self.streak,
            "streak_signal": self.streak_signal.value,
            "confidence_delta": round(self.confidence_delta, 4),
            "recent_history": [h.to_dict() for h in self.recent_history],
            "explanation": self.explanation,
        }
