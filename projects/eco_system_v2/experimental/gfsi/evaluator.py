"""
experimental/gfsi/evaluator.py — 일일 기록 + 선행성 분석 + 백테스트

기능:
  1. 일일 GFSI 결과를 JSON으로 저장
  2. 과거 기록 로드 + 변화 추적
  3. 채널별 VIX 선행/후행 분석 (Granger 인과, cross-correlation)
  4. N일 후 실제 수익률과 비교하여 예측력 검증
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .domain import (
    GRANGER_P_VALUE,
    LEAD_LAG_MAX_DAYS,
    Channel,
    DailyEvaluation,
    GFSIResult,
    LeadLagResult,
)

logger = logging.getLogger(__name__)

OUTPUTS_DIR = Path(__file__).parent / "outputs"


def save_daily(result: GFSIResult, raw_data: dict | None = None) -> Path:
    """일일 GFSI 결과를 JSON으로 저장.

    파일명: gfsi_YYYY-MM-DD.json
    """
    OUTPUTS_DIR.mkdir(exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = OUTPUTS_DIR / f"gfsi_{date_str}.json"

    payload = {
        "result": result.to_dict(),
        "raw_data": raw_data or {},
    }

    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("GFSI saved: %s", path)
    return path


def load_history(days: int = 30) -> list[dict]:
    """과거 GFSI 기록을 날짜순으로 로드.

    Returns:
        [{date, result, raw_data}, ...] 오래된 것부터
    """
    if not OUTPUTS_DIR.exists():
        return []

    files = sorted(OUTPUTS_DIR.glob("gfsi_*.json"))[-days:]
    history: list[dict] = []

    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            date = f.stem.replace("gfsi_", "")
            data["date"] = date
            history.append(data)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load %s: %s", f, e)

    return history


def compute_daily_eval(
    current: GFSIResult,
    history: list[dict],
) -> DailyEvaluation:
    """현재 결과와 전일 기록을 비교하여 DailyEvaluation 생성."""
    today = datetime.now().strftime("%Y-%m-%d")
    gfsi_change = 0.0
    vix_change = 0.0

    if history:
        prev = history[-1].get("result", {})
        prev_score = prev.get("gfsi_score", current.score)
        prev_vix = prev.get("vix_current", current.vix_current)
        gfsi_change = current.score - prev_score
        vix_change = current.vix_current - prev_vix

    return DailyEvaluation(
        date=today,
        gfsi=current,
        vix_change_1d=round(vix_change, 2),
        gfsi_change_1d=round(gfsi_change, 2),
    )


def analyze_lead_lag(history: list[dict], min_days: int = 20) -> list[LeadLagResult]:
    """채널별 VIX 선행/후행 분석.

    최소 min_days 일의 기록이 필요.
    numpy/scipy 가 있으면 Granger 인과, 없으면 cross-correlation만.
    """
    if len(history) < min_days:
        logger.info(
            "Lead-lag analysis needs %d+ days, got %d. Skipping.",
            min_days, len(history),
        )
        return []

    try:
        import numpy as np
    except ImportError:
        logger.warning("numpy not available — lead-lag analysis skipped")
        return []

    # 시계열 추출
    vix_series = []
    channel_series: dict[str, list[float]] = {ch.value: [] for ch in Channel}

    for entry in history:
        result = entry.get("result", {})
        vix_series.append(result.get("vix_current", 0.0))
        for ch_data in result.get("channels", []):
            ch_name = ch_data.get("channel", "")
            if ch_name in channel_series:
                channel_series[ch_name].append(ch_data.get("score", 50.0))

    vix_arr = np.array(vix_series)
    results: list[LeadLagResult] = []

    for ch in Channel:
        ch_arr = np.array(channel_series.get(ch.value, []))

        if len(ch_arr) != len(vix_arr) or len(ch_arr) < min_days:
            continue

        # Cross-correlation at different lags
        best_lag = 0
        best_corr = 0.0

        for lag in range(-LEAD_LAG_MAX_DAYS, LEAD_LAG_MAX_DAYS + 1):
            if lag > 0:
                # 채널이 lag일 선행
                x = ch_arr[:-lag] if lag > 0 else ch_arr
                y = vix_arr[lag:] if lag > 0 else vix_arr
            elif lag < 0:
                x = ch_arr[-lag:]
                y = vix_arr[:lag]
            else:
                x, y = ch_arr, vix_arr

            if len(x) < 10:
                continue

            corr = float(np.corrcoef(x, y)[0, 1])
            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag

        # Granger causality (simplified: OLS F-test)
        p_value = _simple_granger(ch_arr, vix_arr, max_lag=5)

        # VIX 설명력 (R²)
        r_sq = _r_squared(ch_arr, vix_arr)
        residual = 1.0 - r_sq

        results.append(LeadLagResult(
            channel=ch,
            optimal_lag_days=best_lag,
            correlation=round(best_corr, 4),
            granger_p_value=round(p_value, 4),
            is_significant=p_value < GRANGER_P_VALUE,
            r_squared=round(r_sq, 4),
            residual_info=round(residual, 4),
        ))

    return results


def _simple_granger(x: Any, y: Any, max_lag: int = 5) -> float:
    """간단한 Granger 인과 테스트 (OLS 기반).

    H0: x가 y를 Granger-cause하지 않음
    Returns: p-value (낮을수록 x→y 인과 가능성 높음)
    """
    import numpy as np

    n = len(y)
    if n < max_lag + 10:
        return 1.0

    # Restricted model: y(t) = a + b*y(t-1) + ... + b*y(t-p)
    # Unrestricted: y(t) = a + b*y(t-1) + ... + c*x(t-1) + ... + c*x(t-p)
    y_col = y[max_lag:]
    T = len(y_col)

    # 구성 행렬
    restricted = np.ones((T, max_lag + 1))
    unrestricted = np.ones((T, 2 * max_lag + 1))

    for lag in range(1, max_lag + 1):
        restricted[:, lag] = y[max_lag - lag: n - lag]
        unrestricted[:, lag] = y[max_lag - lag: n - lag]
        unrestricted[:, max_lag + lag] = x[max_lag - lag: n - lag]

    try:
        # OLS
        b_r = np.linalg.lstsq(restricted, y_col, rcond=None)[0]
        b_u = np.linalg.lstsq(unrestricted, y_col, rcond=None)[0]

        ssr_r = float(np.sum((y_col - restricted @ b_r) ** 2))
        ssr_u = float(np.sum((y_col - unrestricted @ b_u) ** 2))

        # F-test
        df1 = max_lag
        df2 = T - 2 * max_lag - 1
        if df2 <= 0 or ssr_u <= 0:
            return 1.0

        f_stat = ((ssr_r - ssr_u) / df1) / (ssr_u / df2)

        # F-distribution approximation (scipy 없이)
        # 간단 근사: f_stat > 3.0이면 대략 p < 0.05
        if f_stat > 4.0:
            return 0.01
        if f_stat > 3.0:
            return 0.04
        if f_stat > 2.0:
            return 0.10
        return 0.50
    except (np.linalg.LinAlgError, ValueError):
        return 1.0


def _r_squared(x: Any, y: Any) -> float:
    """단순 선형 R² (VIX 설명력)."""
    import numpy as np

    if len(x) < 5:
        return 0.0
    corr = np.corrcoef(x, y)[0, 1]
    return float(corr ** 2)


def generate_report(
    evaluation: DailyEvaluation,
    lead_lag: list[LeadLagResult] | None = None,
) -> str:
    """일일 평가 리포트 텍스트 생성."""
    lines: list[str] = []
    g = evaluation.gfsi

    lines.append(f"# GFSI Daily Report — {evaluation.date}")
    lines.append("")
    lines.append(f"## 종합: {g.score:.1f} ({g.level.value})")
    lines.append(f"VIX: {g.vix_current:.1f} | "
                 f"GFSI Δ1d: {evaluation.gfsi_change_1d:+.1f} | "
                 f"VIX Δ1d: {evaluation.vix_change_1d:+.1f}")
    lines.append("")

    # 채널별 점수
    lines.append("## 채널별 점수")
    lines.append("| 채널 | 점수 | 시그널 | 품질 |")
    lines.append("|------|------|--------|------|")
    for ch in g.channels:
        lines.append(
            f"| {ch.channel.value} | {ch.score:.1f} | {ch.signal} | "
            f"{ch.data_quality:.0%} |"
        )
    lines.append("")

    # 선행성 분석
    if lead_lag:
        lines.append("## 선행/후행 분석 (채널 → VIX)")
        lines.append("| 채널 | 최적 lag | 상관 | Granger p | 유의미 | R² | 잔차 |")
        lines.append("|------|---------|------|-----------|--------|-----|------|")
        for ll in lead_lag:
            lag_str = f"+{ll.optimal_lag_days}d" if ll.optimal_lag_days > 0 else f"{ll.optimal_lag_days}d"
            sig = "O" if ll.is_significant else "X"
            lines.append(
                f"| {ll.channel.value} | {lag_str} | {ll.correlation:.3f} | "
                f"{ll.granger_p_value:.3f} | {sig} | {ll.r_squared:.3f} | "
                f"{ll.residual_info:.3f} |"
            )
        lines.append("")

    return "\n".join(lines)
