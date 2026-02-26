"""
domain/consensus.py — ConsensusService (Domain Service)

다수결 + 가중 신뢰도 합의 로직. 순수 함수, 외부 의존성 없음.

규칙: 이 파일은 stdlib 외 import 금지 (anthropic, httpx, yfinance 등 절대 금지).
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime

from .signal import EconomicSignal, Signal


class ConsensusService:
    """
    여러 에이전트의 EconomicSignal을 합의 하나로 집약하는 Domain Service.

    사용법:
        signals = [signal_a, signal_b, ...]
        result = ConsensusService.compute(signals)
    """

    @staticmethod
    def compute(signals: list[EconomicSignal]) -> EconomicSignal:
        """
        다수결 신호 + 동의 에이전트 평균 신뢰도로 합의 EconomicSignal 반환.

        빈 리스트 → NEUTRAL, confidence=0.0
        """
        if not signals:
            return EconomicSignal(
                agent="consensus",
                signal=Signal.NEUTRAL,
                confidence=0.0,
                rationale="에이전트 응답 없음",
                timestamp=datetime.now().isoformat(),
            )

        # 다수결 신호 결정
        signal_counts: Counter[Signal] = Counter(s.signal for s in signals)
        majority_signal: Signal = signal_counts.most_common(1)[0][0]

        # 다수결 신호에 동의한 에이전트만 신뢰도 평균
        agreeing = [s for s in signals if s.signal == majority_signal]
        avg_confidence = sum(s.confidence for s in agreeing) / len(agreeing)

        # 합의 근거 요약
        names = ", ".join(s.agent for s in agreeing)
        total = len(signals)
        rationale = (
            f"{majority_signal.value} 합의 "
            f"({len(agreeing)}/{total}명 동의: {names}), "
            f"평균 신뢰도 {avg_confidence:.0%}"
        )

        return EconomicSignal(
            agent="consensus",
            signal=majority_signal,
            confidence=round(avg_confidence, 4),
            rationale=rationale,
            timestamp=datetime.now().isoformat(),
        )
