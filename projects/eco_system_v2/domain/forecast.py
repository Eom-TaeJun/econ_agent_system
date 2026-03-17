"""
domain/forecast.py — 전망 관련 Value Objects

HorizonType, ForecastResult (LLM 전망), LASSOForecast (정량 예측)

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


@dataclass(frozen=True)
class LASSOForecast:
    """
    LASSO 정량 예측 결과 — Value Object (불변).

    predicted_return: 예측된 전방 수익률 (%)
    signal: 예측 방향 (수익률 기반)
    confidence: 모델 신뢰도 (R² 기반)
    key_drivers: 주요 동인 변수와 계수 — tuple((변수명, 계수), ...)
    r_squared: 모델 결정계수 (0~1)
    n_observations: 학습 관측치 수
    n_selected: LASSO가 선택한 변수 수
    explanation: 사람이 읽는 설명
    """

    predicted_return: float
    signal: Signal
    confidence: float
    key_drivers: tuple[tuple[str, float], ...]
    r_squared: float
    n_observations: int
    n_selected: int
    explanation: str

    def to_dict(self) -> dict:
        return {
            "predicted_return": round(self.predicted_return, 4),
            "signal": self.signal.value,
            "confidence": round(self.confidence, 4),
            "key_drivers": [
                {"feature": f, "coefficient": round(c, 4)}
                for f, c in self.key_drivers
            ],
            "r_squared": round(self.r_squared, 4),
            "n_observations": self.n_observations,
            "n_selected": self.n_selected,
            "explanation": self.explanation,
        }
