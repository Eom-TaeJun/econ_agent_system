"""
domain/scorecard.py — Signal Accountability (Scorecard) Value Objects

과거 신호가 실제로 맞았는지 평가하기 위한 도메인 객체.
규칙: stdlib만 import (domain 순수성 유지).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Outcome(str, Enum):
    """신호 평가 결과."""
    HIT = "HIT"
    MISS = "MISS"
    PENDING = "PENDING"
    NO_DATA = "NO_DATA"


@dataclass(frozen=True)
class SignalEvaluation:
    """개별 신호 1건의 평가 결과."""
    date: str
    source: str          # "consensus", "analysis", "research", "quant" 등
    signal: str          # "BULLISH" / "NEUTRAL" / "BEARISH"
    confidence: float
    actual_return_pct: float | None  # SPX 수익률 (%), None이면 미확정
    outcome: Outcome
    horizon_days: int

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "source": self.source,
            "signal": self.signal,
            "confidence": self.confidence,
            "actual_return_pct": self.actual_return_pct,
            "outcome": self.outcome.value,
            "horizon_days": self.horizon_days,
        }


@dataclass(frozen=True)
class SourceMetrics:
    """특정 소스(에이전트 또는 합의)의 적중률 집계."""
    source: str
    total: int
    hits: int
    misses: int
    hit_rate: float
    confidence_weighted_hit_rate: float
    avg_confidence_when_hit: float
    avg_confidence_when_miss: float

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "total": self.total,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hit_rate, 4),
            "confidence_weighted_hit_rate": round(self.confidence_weighted_hit_rate, 4),
            "avg_confidence_when_hit": round(self.avg_confidence_when_hit, 4),
            "avg_confidence_when_miss": round(self.avg_confidence_when_miss, 4),
        }


# ============================================================================
# 진단(Diagnostics) VO — 스코어카드 해석을 위한 추가 분석
# ============================================================================


@dataclass(frozen=True)
class CalibrationBucket:
    """신뢰도 구간별 실제 적중률. 교정(calibration) 분석용."""
    confidence_range: tuple[float, float]  # (0.5, 0.6) = 50~60%
    total: int
    hits: int
    actual_hit_rate: float
    expected_confidence: float   # 이 구간의 평균 신뢰도
    calibration_gap: float       # actual - expected (양수=과소신뢰, 음수=과신)

    def to_dict(self) -> dict:
        return {
            "confidence_range": list(self.confidence_range),
            "total": self.total,
            "hits": self.hits,
            "actual_hit_rate": round(self.actual_hit_rate, 4),
            "expected_confidence": round(self.expected_confidence, 4),
            "calibration_gap": round(self.calibration_gap, 4),
        }


@dataclass(frozen=True)
class DirectionalBreakdown:
    """방향별 적중률. BULLISH/BEARISH 비대칭 분석용."""
    source: str
    bullish_total: int
    bullish_hits: int
    bullish_hit_rate: float
    bearish_total: int
    bearish_hits: int
    bearish_hit_rate: float
    neutral_total: int
    neutral_hits: int
    neutral_hit_rate: float
    dominant_bias: str   # 가장 많이 낸 방향

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "bullish": {"total": self.bullish_total, "hits": self.bullish_hits, "hit_rate": round(self.bullish_hit_rate, 4)},
            "bearish": {"total": self.bearish_total, "hits": self.bearish_hits, "hit_rate": round(self.bearish_hit_rate, 4)},
            "neutral": {"total": self.neutral_total, "hits": self.neutral_hits, "hit_rate": round(self.neutral_hit_rate, 4)},
            "dominant_bias": self.dominant_bias,
        }


@dataclass(frozen=True)
class MarketContextMetrics:
    """특정 시장 환경에서의 적중률. 레짐/금리/VIX 구간별 분석용."""
    context_label: str   # "금리인하기", "VIX>20", "Bear(High Vol)" 등
    total: int
    hits: int
    hit_rate: float
    avg_return: float    # 해당 구간 평균 실현 수익률 (%)

    def to_dict(self) -> dict:
        return {
            "context_label": self.context_label,
            "total": self.total,
            "hits": self.hits,
            "hit_rate": round(self.hit_rate, 4),
            "avg_return": round(self.avg_return, 4),
        }


@dataclass(frozen=True)
class RelativePerformance:
    """US vs 국제 상대성과. 미국 예외주의 가설 검증용."""
    period_label: str              # "2026 Q1", "최근 20거래일" 등
    spx_return: float              # SPX 수익률 (%)
    efa_return: float              # MSCI EAFE 수익률 (선진국 ex-US, %)
    eem_return: float              # MSCI EM 수익률 (신흥국, %)
    dxy_change: float              # 달러 인덱스 변화율 (%)
    us_vs_efa: float               # SPX - EFA (양수=US 아웃퍼폼)
    us_vs_eem: float               # SPX - EEM (양수=US 아웃퍼폼)
    regime_label: str              # "US 예외주의", "글로벌 동조", "US 언더퍼폼" 등

    def to_dict(self) -> dict:
        return {
            "period_label": self.period_label,
            "spx_return": round(self.spx_return, 2),
            "efa_return": round(self.efa_return, 2),
            "eem_return": round(self.eem_return, 2),
            "dxy_change": round(self.dxy_change, 2),
            "us_vs_efa": round(self.us_vs_efa, 2),
            "us_vs_eem": round(self.us_vs_eem, 2),
            "regime_label": self.regime_label,
        }


@dataclass(frozen=True)
class NarrativeAssessment:
    """거시 내러티브(가설) 평가. 데이터가 가설을 지지/반박하는지."""
    hypothesis: str                # "미국 예외주의", "금리인하 = 강세" 등
    verdict: str                   # "지지", "약화", "반박", "불확실"
    evidence: tuple[str, ...]      # 근거 목록
    signal_implication: str        # 신호 체계에 대한 시사점

    def to_dict(self) -> dict:
        return {
            "hypothesis": self.hypothesis,
            "verdict": self.verdict,
            "evidence": list(self.evidence),
            "signal_implication": self.signal_implication,
        }


@dataclass(frozen=True)
class ScorecardDiagnostics:
    """스코어카드 진단 — 단순 적중률 너머의 해석."""
    calibration: tuple[CalibrationBucket, ...]
    directional: tuple[DirectionalBreakdown, ...]
    market_contexts: tuple[MarketContextMetrics, ...]
    consecutive_miss_streak: int   # 현재 연속 MISS 횟수
    brier_score: float             # 확률 교정 품질 (0=완벽, 1=최악)
    warnings: tuple[str, ...]      # 운용 경고 메시지
    relative_performance: tuple[RelativePerformance, ...] = ()
    narratives: tuple[NarrativeAssessment, ...] = ()

    def to_dict(self) -> dict:
        return {
            "calibration": [b.to_dict() for b in self.calibration],
            "directional": [d.to_dict() for d in self.directional],
            "market_contexts": [m.to_dict() for m in self.market_contexts],
            "consecutive_miss_streak": self.consecutive_miss_streak,
            "brier_score": round(self.brier_score, 4),
            "warnings": list(self.warnings),
            "relative_performance": [r.to_dict() for r in self.relative_performance],
            "narratives": [n.to_dict() for n in self.narratives],
        }


@dataclass(frozen=True)
class ScorecardReport:
    """스코어카드 전체 리포트."""
    date_range: tuple[str, str]   # (시작일, 종료일)
    horizon_days: int
    total_evaluated: int
    total_pending: int
    consensus_metrics: SourceMetrics | None
    agent_metrics: tuple[SourceMetrics, ...]
    evaluations: tuple[SignalEvaluation, ...]
    best_agent: str
    worst_agent: str
    explanation: str
    diagnostics: ScorecardDiagnostics | None = None

    def to_dict(self) -> dict:
        return {
            "date_range": list(self.date_range),
            "horizon_days": self.horizon_days,
            "total_evaluated": self.total_evaluated,
            "total_pending": self.total_pending,
            "consensus_metrics": self.consensus_metrics.to_dict() if self.consensus_metrics else None,
            "agent_metrics": [m.to_dict() for m in self.agent_metrics],
            "evaluations": [e.to_dict() for e in self.evaluations],
            "best_agent": self.best_agent,
            "worst_agent": self.worst_agent,
            "explanation": self.explanation,
            "diagnostics": self.diagnostics.to_dict() if self.diagnostics else None,
        }
