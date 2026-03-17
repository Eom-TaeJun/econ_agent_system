"""
domain/consensus.py — ConsensusService (Domain Service)

신뢰도 가중 합의 로직. 순수 함수, 외부 의존성 없음.

방법론:
  1. 신뢰도 가중 투표: 각 에이전트의 confidence가 투표 가중치
  2. 마진 계산: 1위와 2위 점수 차이 → 결정력 지표
  3. ConsensusBreakdown: 어떤 에이전트가 어떻게 기여했는지 투명하게 기록

규칙: 이 파일은 stdlib 외 import 금지 (anthropic, httpx, yfinance 등 절대 금지).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .signal import EconomicSignal, Signal


# ============================================================================
# Value Objects
# ============================================================================

@dataclass(frozen=True)
class AgentContribution:
    """합의 과정에서 개별 에이전트의 기여 기록."""

    agent: str
    signal: Signal
    confidence: float
    weight: float                # 가중치 (= confidence)
    agreed_with_consensus: bool  # 최종 합의와 동일 방향인지

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "signal": self.signal.value,
            "confidence": self.confidence,
            "weight": round(self.weight, 4),
            "agreed": self.agreed_with_consensus,
        }


@dataclass(frozen=True)
class ConsensusBreakdown:
    """합의 과정의 투명한 분해 — 납득 가능한 근거를 제공한다."""

    method: str                                        # "confidence_weighted"
    signal_scores: tuple[tuple[str, float], ...]       # (BULLISH, 1.45), ...
    contributions: tuple[AgentContribution, ...]       # 에이전트별 기여
    agreement_ratio: float                             # 동의 비율 (0~1)
    margin: float                                      # 결정 마진 (0~1)
    final_confidence: float                            # 최종 신뢰도
    explanation: str                                   # 사람이 읽는 설명

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "signal_scores": {k: round(v, 4) for k, v in self.signal_scores},
            "contributions": [c.to_dict() for c in self.contributions],
            "agreement_ratio": round(self.agreement_ratio, 4),
            "margin": round(self.margin, 4),
            "final_confidence": round(self.final_confidence, 4),
            "explanation": self.explanation,
        }


# ============================================================================
# ConsensusService
# ============================================================================

class ConsensusService:
    """
    여러 에이전트의 EconomicSignal을 합의 하나로 집약하는 Domain Service.

    방법: 신뢰도 가중 투표
      - 각 에이전트의 confidence가 투표 가중치
      - Signal별 가중 점수 합산 → 최고 점수 Signal 채택
      - 최종 신뢰도 = 동의 에이전트 가중 평균 × 결정력 보정

    사용법:
        signals = [signal_a, signal_b, ...]
        consensus, breakdown = ConsensusService.compute(signals)
    """

    @staticmethod
    def compute(
        signals: list[EconomicSignal],
    ) -> tuple[EconomicSignal, ConsensusBreakdown]:
        """
        신뢰도 가중 합의를 계산한다.

        Returns:
            (EconomicSignal, ConsensusBreakdown) 튜플
        """
        if not signals:
            return _empty_result()

        # 1. Signal별 가중 점수 합산
        scores: dict[Signal, float] = {
            Signal.BULLISH: 0.0,
            Signal.NEUTRAL: 0.0,
            Signal.BEARISH: 0.0,
        }
        for s in signals:
            scores[s.signal] += s.confidence

        # 2. 최고 점수 Signal 채택
        sorted_signals = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        winner: Signal = sorted_signals[0][0]
        winner_score: float = sorted_signals[0][1]
        runner_up_score: float = sorted_signals[1][1] if len(sorted_signals) > 1 else 0.0
        total_score = sum(scores.values())

        # 3. 마진: 결정이 얼마나 확실한가 (0~1)
        margin = (winner_score - runner_up_score) / total_score if total_score > 0 else 0.0

        # 4. 동의/반대 분류
        agreeing = [s for s in signals if s.signal == winner]
        dissenting = [s for s in signals if s.signal != winner]
        agreement_ratio = len(agreeing) / len(signals)

        # 5. 최종 신뢰도 산출
        #    = 동의 에이전트 가중평균 신뢰도 × 마진 보정
        #    마진이 클수록 확신, 작으면 감쇄
        if agreeing:
            weighted_sum = sum(s.confidence ** 2 for s in agreeing)
            weight_total = sum(s.confidence for s in agreeing)
            base_confidence = weighted_sum / weight_total  # 신뢰도가 높은 에이전트에 더 가중
        else:
            base_confidence = 0.0

        # 마진 보정: 마진 0이면 ×0.7, 마진 1이면 ×1.0
        margin_factor = 0.7 + 0.3 * min(1.0, margin * 2)
        final_confidence = round(min(1.0, base_confidence * margin_factor), 4)

        # 6. 에이전트별 기여도 기록
        contributions = tuple(
            AgentContribution(
                agent=s.agent,
                signal=s.signal,
                confidence=s.confidence,
                weight=s.confidence,
                agreed_with_consensus=(s.signal == winner),
            )
            for s in signals
        )

        # 7. 납득 가능한 설명 생성
        explanation = _build_explanation(
            winner=winner,
            scores=scores,
            agreeing=agreeing,
            dissenting=dissenting,
            margin=margin,
            base_confidence=base_confidence,
            margin_factor=margin_factor,
            final_confidence=final_confidence,
            total=len(signals),
        )

        # 8. 간결한 rationale (EconomicSignal용)
        agree_names = ", ".join(s.agent for s in agreeing)
        rationale = (
            f"{winner.value} 합의 "
            f"({len(agreeing)}/{len(signals)}명 동의: {agree_names}), "
            f"신뢰도 {final_confidence:.0%}, 마진 {margin:.0%}"
        )

        signal_scores_tuple = tuple(
            (sig.value, round(sc, 4)) for sig, sc in sorted_signals
        )

        breakdown = ConsensusBreakdown(
            method="confidence_weighted",
            signal_scores=signal_scores_tuple,
            contributions=contributions,
            agreement_ratio=round(agreement_ratio, 4),
            margin=round(margin, 4),
            final_confidence=final_confidence,
            explanation=explanation,
        )

        consensus_signal = EconomicSignal(
            agent="consensus",
            signal=winner,
            confidence=final_confidence,
            rationale=rationale,
            timestamp=datetime.now().isoformat(),
        )

        return consensus_signal, breakdown


# ============================================================================
# 내부 함수
# ============================================================================

def _build_explanation(
    winner: Signal,
    scores: dict[Signal, float],
    agreeing: list[EconomicSignal],
    dissenting: list[EconomicSignal],
    margin: float,
    base_confidence: float,
    margin_factor: float,
    final_confidence: float,
    total: int,
) -> str:
    """사람이 읽을 수 있는 합의 과정 설명."""
    lines: list[str] = []

    # 1. 가중 투표 결과
    score_parts = []
    for sig in [Signal.BULLISH, Signal.NEUTRAL, Signal.BEARISH]:
        sc = scores[sig]
        if sc > 0:
            score_parts.append(f"{sig.value} {sc:.2f}")
    lines.append(f"가중 투표: {' > '.join(score_parts)}")

    # 2. 결정 마진
    if margin > 0.5:
        margin_desc = "매우 확실"
    elif margin > 0.25:
        margin_desc = "확실"
    elif margin > 0.1:
        margin_desc = "근소한 차이"
    else:
        margin_desc = "매우 근소 (주의)"
    lines.append(f"마진: {margin:.0%} ({margin_desc})")

    # 3. 동의 에이전트
    for s in agreeing:
        lines.append(f"  [동의] {s.agent}: {s.signal.value} ({s.confidence:.0%})")

    # 4. 반대 에이전트 (있으면)
    for s in dissenting:
        reason_preview = s.rationale[:80] if s.rationale else ""
        lines.append(
            f"  [반대] {s.agent}: {s.signal.value} ({s.confidence:.0%})"
            + (f' — "{reason_preview}"' if reason_preview else "")
        )

    # 5. 신뢰도 산출 과정
    lines.append(
        f"신뢰도 산출: 동의 가중평균 {base_confidence:.0%} "
        f"x 마진보정 {margin_factor:.2f} = {final_confidence:.0%}"
    )

    return "\n".join(lines)


def _empty_result() -> tuple[EconomicSignal, ConsensusBreakdown]:
    """에이전트 응답 없음."""
    signal = EconomicSignal(
        agent="consensus",
        signal=Signal.NEUTRAL,
        confidence=0.0,
        rationale="에이전트 응답 없음",
        timestamp=datetime.now().isoformat(),
    )
    breakdown = ConsensusBreakdown(
        method="confidence_weighted",
        signal_scores=(
            ("NEUTRAL", 0.0),
            ("BULLISH", 0.0),
            ("BEARISH", 0.0),
        ),
        contributions=(),
        agreement_ratio=0.0,
        margin=0.0,
        final_confidence=0.0,
        explanation="에이전트 응답 없음 — 합의 불가",
    )
    return signal, breakdown
