"""
infrastructure/persistence/history_reader.py

outputs/ 디렉토리에서 과거 분석 결과를 읽고 현재 결과와 비교한다.

인터페이스:
  load_history(output_dir, limit) -> list[TrendSnapshot]
  compare_with_history(current_result, output_dir) -> TrendComparison | None
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from domain.signal import Signal
from domain.trend import (
    Direction,
    SignalChange,
    TrendComparison,
    TrendSnapshot,
    classify_direction,
)

logger = logging.getLogger(__name__)

# 최근 이력 최대 개수
_MAX_HISTORY = 10


def load_history(output_dir: str = "outputs", limit: int = _MAX_HISTORY) -> list[TrendSnapshot]:
    """
    outputs/eco_*.json을 날짜 역순으로 읽어 TrendSnapshot 리스트를 반환한다.

    limit: 최대 개수 (기본 10)
    """
    output_path = Path(output_dir)
    if not output_path.exists():
        return []

    files = sorted(output_path.glob("eco_*.json"), reverse=True)
    snapshots: list[TrendSnapshot] = []

    for fp in files[:limit * 2]:  # 파싱 실패 대비 여유
        try:
            snapshot = _parse_snapshot(fp)
            if snapshot:
                snapshots.append(snapshot)
                if len(snapshots) >= limit:
                    break
        except Exception as e:
            logger.debug(f"[history] 파싱 스킵: {fp.name} — {e}")

    return snapshots


def compare_with_history(
    current_result: dict,
    output_dir: str = "outputs",
) -> TrendComparison | None:
    """
    현재 결과와 과거 이력을 비교해 TrendComparison을 반환한다.

    current_result: EcoResult.to_dict() 결과
    이력이 없으면 None 반환.
    """
    history = load_history(output_dir)
    if not history:
        return None

    current_date = current_result.get("date", "")
    current_signal = Signal(current_result["consensus_signal"])
    current_confidence = current_result["consensus_confidence"]

    # 직전 결과 (현재 날짜와 다른 첫 번째, 또는 같은 날이라도 이전 것)
    prev = history[0]

    # 합의 방향 변화
    consensus_dir = classify_direction(prev.consensus_signal, current_signal)

    # 신뢰도 변화
    confidence_delta = current_confidence - prev.consensus_confidence

    # 에이전트별 변화 비교
    signal_changes = _compare_agents(current_result, prev)

    # 연속 횟수 (streak) 계산
    streak, streak_signal = _calculate_streak(current_signal, history)

    # 설명 생성
    explanation = _build_explanation(
        current_signal=current_signal,
        current_confidence=current_confidence,
        prev=prev,
        consensus_dir=consensus_dir,
        confidence_delta=confidence_delta,
        signal_changes=signal_changes,
        streak=streak,
        streak_signal=streak_signal,
    )

    return TrendComparison(
        current_date=current_date,
        previous_date=prev.date,
        consensus_direction=consensus_dir,
        signal_changes=tuple(signal_changes),
        streak=streak,
        streak_signal=streak_signal,
        confidence_delta=round(confidence_delta, 4),
        recent_history=tuple(history[:5]),  # 최근 5개만
        explanation=explanation,
    )


# ============================================================================
# 내부 함수
# ============================================================================

def _parse_snapshot(filepath: Path) -> TrendSnapshot | None:
    """JSON 파일 하나를 TrendSnapshot으로 파싱."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "consensus_signal" not in data:
        return None

    agent_signals = tuple(
        (a["agent"], a["signal"], a.get("confidence", 0.0))
        for a in data.get("agent_signals", [])
    )

    return TrendSnapshot(
        date=data.get("date", filepath.stem),
        consensus_signal=Signal(data["consensus_signal"]),
        consensus_confidence=data.get("consensus_confidence", 0.0),
        agent_signals=agent_signals,
    )


def _compare_agents(
    current_result: dict,
    prev: TrendSnapshot,
) -> list[SignalChange]:
    """에이전트별 신호 변화를 비교한다."""
    # 이전 에이전트 맵
    prev_map: dict[str, tuple[Signal, float]] = {}
    for agent, sig_str, conf in prev.agent_signals:
        prev_map[agent] = (Signal(sig_str), conf)

    changes: list[SignalChange] = []
    for agent_data in current_result.get("agent_signals", []):
        agent = agent_data["agent"]
        curr_signal = Signal(agent_data["signal"])
        curr_conf = agent_data.get("confidence", 0.0)

        if agent in prev_map:
            prev_signal, prev_conf = prev_map[agent]
            direction = classify_direction(prev_signal, curr_signal)
            changes.append(SignalChange(
                agent=agent,
                previous_signal=prev_signal,
                current_signal=curr_signal,
                previous_confidence=prev_conf,
                current_confidence=curr_conf,
                direction=direction,
            ))

    return changes


def _calculate_streak(
    current_signal: Signal,
    history: list[TrendSnapshot],
) -> tuple[int, Signal]:
    """현재 신호와 같은 방향의 연속 횟수를 계산한다."""
    streak = 1  # 현재 포함
    for snap in history:
        if snap.consensus_signal == current_signal:
            streak += 1
        else:
            break
    return streak, current_signal


def _build_explanation(
    current_signal: Signal,
    current_confidence: float,
    prev: TrendSnapshot,
    consensus_dir: Direction,
    confidence_delta: float,
    signal_changes: list[SignalChange],
    streak: int,
    streak_signal: Signal,
) -> str:
    """사람이 읽는 트렌드 비교 설명."""
    lines: list[str] = []

    # 1. 합의 변화
    if consensus_dir == Direction.UNCHANGED:
        lines.append(
            f"합의 유지: {current_signal.value} "
            f"(직전 {prev.date}과 동일)"
        )
    elif consensus_dir == Direction.REVERSED:
        lines.append(
            f"합의 반전: {prev.consensus_signal.value} → {current_signal.value} "
            f"(직전 {prev.date} 대비)"
        )
    else:
        verb = "상향" if consensus_dir == Direction.UPGRADED else "하향"
        lines.append(
            f"합의 {verb}: {prev.consensus_signal.value} → {current_signal.value} "
            f"(직전 {prev.date} 대비)"
        )

    # 2. 신뢰도 변화
    if abs(confidence_delta) >= 0.05:
        direction = "상승" if confidence_delta > 0 else "하락"
        lines.append(
            f"신뢰도 {direction}: {prev.consensus_confidence:.0%} → {current_confidence:.0%} "
            f"({confidence_delta:+.0%}p)"
        )
    else:
        lines.append(f"신뢰도 유사: {current_confidence:.0%} (변화 {confidence_delta:+.0%}p)")

    # 3. 연속 횟수
    if streak >= 3:
        lines.append(f"{streak_signal.value} {streak}회 연속 — 추세 고착화")
    elif streak == 2:
        lines.append(f"{streak_signal.value} 2회 연속")

    # 4. 에이전트별 주요 변화
    notable = [c for c in signal_changes if c.direction != Direction.UNCHANGED]
    if notable:
        lines.append("에이전트 변화:")
        for c in notable:
            conf_delta = c.current_confidence - c.previous_confidence
            lines.append(
                f"  {c.agent}: {c.previous_signal.value}→{c.current_signal.value} "
                f"({c.direction.value}, 신뢰도 {conf_delta:+.0%}p)"
            )

    return "\n".join(lines)
