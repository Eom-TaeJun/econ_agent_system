"""
infrastructure/analysis/scorecard_service.py

과거 신호를 실제 SPX 수익률과 비교해 에이전트별/합의별 적중률을 산출한다.
진단(Diagnostics): 교정 분석, 방향 비대칭, 시장 환경별 적중률, 연속 미스 감지.

인터페이스:
  evaluate_signals(output_dir, horizon_days) -> ScorecardReport
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from domain.scorecard import (
    CalibrationBucket,
    DirectionalBreakdown,
    MarketContextMetrics,
    NarrativeAssessment,
    Outcome,
    RelativePerformance,
    ScorecardDiagnostics,
    ScorecardReport,
    SignalEvaluation,
    SourceMetrics,
)
from domain.thresholds import (
    SCORECARD_BEARISH_THRESHOLD,
    SCORECARD_BULLISH_THRESHOLD,
    SCORECARD_HORIZON_DAYS,
)
from infrastructure.persistence.history_reader import load_history

logger = logging.getLogger(__name__)


def evaluate_signals(
    output_dir: str = "outputs",
    horizon_days: int | None = None,
) -> ScorecardReport:
    """
    과거 신호를 SPX 실제 수익률과 비교해 스코어카드를 생성한다.

    output_dir: 과거 스냅샷이 저장된 디렉토리
    horizon_days: 평가 기간 (거래일). None이면 기본값 20.
    """
    horizon = horizon_days or int(SCORECARD_HORIZON_DAYS.value)

    # 1. 과거 스냅샷 로드
    snapshots = load_history(output_dir, limit=200)
    if not snapshots:
        return _empty_report(horizon)

    # 2. 날짜별 중복 제거 (같은 날 여러 실행 시 최신 1개만)
    seen_dates: set[str] = set()
    unique_snapshots = []
    for snap in snapshots:  # 이미 역순 정렬
        if snap.date not in seen_dates:
            seen_dates.add(snap.date)
            unique_snapshots.append(snap)

    # 3. SPX 종가 로드
    prices = _fetch_spx_prices(unique_snapshots, horizon)
    if not prices:
        return _empty_report(horizon)

    # 4. 각 스냅샷 평가
    all_evaluations: list[SignalEvaluation] = []
    for snap in unique_snapshots:
        evals = _evaluate_one(snap, prices, horizon)
        all_evaluations.extend(evals)

    # 5. 평가 완료/대기 분리
    evaluated = [e for e in all_evaluations if e.outcome in (Outcome.HIT, Outcome.MISS)]

    if not evaluated:
        # 평가 완료 건이 없어도 PENDING 진단은 유용
        diagnostics = _build_diagnostics_pending(all_evaluations, output_dir)
        return ScorecardReport(
            date_range=_date_range(seen_dates),
            horizon_days=horizon,
            total_evaluated=0,
            total_pending=len([e for e in all_evaluations
                              if e.outcome == Outcome.PENDING and e.source == "consensus"]),
            consensus_metrics=None,
            agent_metrics=(),
            evaluations=tuple(all_evaluations),
            best_agent="",
            worst_agent="",
            explanation="평가 완료 건 없음 (모두 PENDING). 진단 섹션에 현재 상태 분석 포함.",
            diagnostics=diagnostics,
        )

    # 6. 집계
    consensus_evals = [e for e in evaluated if e.source == "consensus"]
    consensus_metrics = _aggregate(consensus_evals, "consensus") if consensus_evals else None

    agent_names = sorted({e.source for e in evaluated if e.source != "consensus"})
    agent_metrics_list = []
    for name in agent_names:
        agent_evals = [e for e in evaluated if e.source == name]
        if agent_evals:
            agent_metrics_list.append(_aggregate(agent_evals, name))

    agent_metrics = tuple(agent_metrics_list)

    best_agent = ""
    worst_agent = ""
    if agent_metrics:
        best_agent = max(agent_metrics, key=lambda m: m.hit_rate).source
        worst_agent = min(agent_metrics, key=lambda m: m.hit_rate).source

    # 7. 진단 분석
    raw_data = _load_raw_snapshots(output_dir, seen_dates)
    diagnostics = _build_diagnostics(evaluated, all_evaluations, raw_data)

    # 8. 설명 (진단 포함)
    explanation = _build_explanation(
        consensus_metrics=consensus_metrics,
        agent_metrics=agent_metrics,
        total_evaluated=len(consensus_evals),
        total_pending=len([e for e in all_evaluations
                          if e.outcome == Outcome.PENDING and e.source == "consensus"]),
        horizon=horizon,
        best_agent=best_agent,
        worst_agent=worst_agent,
        diagnostics=diagnostics,
    )

    return ScorecardReport(
        date_range=_date_range(seen_dates),
        horizon_days=horizon,
        total_evaluated=len(consensus_evals),
        total_pending=len([e for e in all_evaluations
                          if e.outcome == Outcome.PENDING and e.source == "consensus"]),
        consensus_metrics=consensus_metrics,
        agent_metrics=agent_metrics,
        evaluations=tuple(all_evaluations),
        best_agent=best_agent,
        worst_agent=worst_agent,
        explanation=explanation,
        diagnostics=diagnostics,
    )


# ============================================================================
# 가격 & 평가 헬퍼
# ============================================================================

def _fetch_spx_prices(snapshots: list, horizon: int) -> dict[str, float]:
    """yfinance로 SPX 종가를 로드한다."""
    try:
        import yfinance as yf
    except ImportError:
        logger.error("yfinance가 설치되어 있지 않습니다.")
        return {}

    if not snapshots:
        return {}

    dates = sorted(snap.date for snap in snapshots)
    try:
        start_date = datetime.strptime(dates[0], "%Y-%m-%d") - timedelta(days=10)
    except ValueError:
        logger.warning(f"날짜 파싱 실패: {dates[0]}")
        return {}

    end_date = datetime.now() + timedelta(days=1)

    try:
        spx = yf.download(
            "^GSPC",
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            progress=False,
        )
    except Exception as e:
        logger.error(f"SPX 데이터 다운로드 실패: {e}")
        return {}

    if spx.empty:
        return {}

    prices: dict[str, float] = {}
    for idx, row in spx.iterrows():
        date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
        close = row["Close"]
        if hasattr(close, "item"):
            close = close.item()
        elif hasattr(close, "values"):
            close = float(close.values[0]) if len(close.values) > 0 else float(close)
        prices[date_str] = float(close)

    return prices


def _find_nearest_price(date_str: str, prices: dict[str, float]) -> float | None:
    """주말/공휴일 처리 — 최대 5일 역방향 탐색."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None
    for offset in range(6):
        candidate = (dt - timedelta(days=offset)).strftime("%Y-%m-%d")
        if candidate in prices:
            return prices[candidate]
    return None


def _find_forward_price(
    date_str: str,
    prices: dict[str, float],
    horizon: int,
) -> float | None:
    """정확히 N 거래일 후 가격을 찾는다."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None
    sorted_dates = sorted(prices.keys())
    start_str = dt.strftime("%Y-%m-%d")
    future_dates = [d for d in sorted_dates if d > start_str]
    if len(future_dates) < horizon:
        return None
    target_date = future_dates[horizon - 1]
    return prices.get(target_date)


def _judge(signal: str, actual_return: float) -> Outcome:
    """신호 vs 실제 수익률 → 적중 판정."""
    bull_thresh = SCORECARD_BULLISH_THRESHOLD.value
    bear_thresh = SCORECARD_BEARISH_THRESHOLD.value

    if signal == "BULLISH":
        return Outcome.HIT if actual_return > bull_thresh else Outcome.MISS
    elif signal == "BEARISH":
        return Outcome.HIT if actual_return < bear_thresh else Outcome.MISS
    else:  # NEUTRAL
        return Outcome.HIT if abs(actual_return) <= bull_thresh else Outcome.MISS


def _evaluate_one(snapshot, prices: dict[str, float], horizon: int) -> list[SignalEvaluation]:
    """스냅샷 1개의 합의 + 에이전트별 신호를 평가한다."""
    evaluations: list[SignalEvaluation] = []

    base_price = _find_nearest_price(snapshot.date, prices)
    if base_price is None:
        return evaluations

    forward_price = _find_forward_price(snapshot.date, prices, horizon)
    actual_return = ((forward_price - base_price) / base_price) * 100 if forward_price else None

    # 합의 평가
    consensus_signal = snapshot.consensus_signal.value
    outcome = _judge(consensus_signal, actual_return) if actual_return is not None else Outcome.PENDING

    evaluations.append(SignalEvaluation(
        date=snapshot.date,
        source="consensus",
        signal=consensus_signal,
        confidence=snapshot.consensus_confidence,
        actual_return_pct=round(actual_return, 4) if actual_return is not None else None,
        outcome=outcome,
        horizon_days=horizon,
    ))

    # 에이전트별 평가
    for agent_name, signal_str, confidence in snapshot.agent_signals:
        agent_outcome = _judge(signal_str, actual_return) if actual_return is not None else Outcome.PENDING
        evaluations.append(SignalEvaluation(
            date=snapshot.date,
            source=agent_name,
            signal=signal_str,
            confidence=confidence,
            actual_return_pct=round(actual_return, 4) if actual_return is not None else None,
            outcome=agent_outcome,
            horizon_days=horizon,
        ))

    return evaluations


def _aggregate(evals: list[SignalEvaluation], source: str) -> SourceMetrics:
    """평가 목록을 집계해 SourceMetrics를 반환한다."""
    hits = [e for e in evals if e.outcome == Outcome.HIT]
    misses = [e for e in evals if e.outcome == Outcome.MISS]
    total = len(hits) + len(misses)

    hit_rate = len(hits) / total if total > 0 else 0.0

    total_weight = sum(e.confidence for e in evals if e.outcome in (Outcome.HIT, Outcome.MISS))
    cw_hit_rate = sum(e.confidence for e in hits) / total_weight if total_weight > 0 else 0.0

    avg_conf_hit = (sum(e.confidence for e in hits) / len(hits)) if hits else 0.0
    avg_conf_miss = (sum(e.confidence for e in misses) / len(misses)) if misses else 0.0

    return SourceMetrics(
        source=source,
        total=total,
        hits=len(hits),
        misses=len(misses),
        hit_rate=hit_rate,
        confidence_weighted_hit_rate=cw_hit_rate,
        avg_confidence_when_hit=avg_conf_hit,
        avg_confidence_when_miss=avg_conf_miss,
    )


# ============================================================================
# 진단(Diagnostics) 분석
# ============================================================================

def _load_raw_snapshots(output_dir: str, dates: set[str]) -> dict[str, dict]:
    """
    outputs/eco_*.json을 읽어 날짜별 원본 데이터를 반환한다.
    market_data, regime 등 전체 정보가 필요할 때 사용.
    """
    output_path = Path(output_dir)
    if not output_path.exists():
        return {}

    raw: dict[str, dict] = {}
    for fp in sorted(output_path.glob("eco_*.json"), reverse=True):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            date = data.get("date", "")
            if date in dates and date not in raw:
                raw[date] = data
        except Exception:
            continue
    return raw


def _build_calibration(evals: list[SignalEvaluation]) -> tuple[CalibrationBucket, ...]:
    """
    신뢰도 구간별 실제 적중률을 계산한다.
    핵심 질문: "70% 신뢰도 신호가 실제로 70% 맞는가?"
    """
    # 합의 신호만 사용 (에이전트별은 중복)
    consensus = [e for e in evals if e.source == "consensus"
                 and e.outcome in (Outcome.HIT, Outcome.MISS)]
    if not consensus:
        return ()

    brackets = [(0.0, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]
    buckets: list[CalibrationBucket] = []

    for lo, hi in brackets:
        bucket_evals = [e for e in consensus if lo <= e.confidence < hi]
        if not bucket_evals:
            continue
        hits = sum(1 for e in bucket_evals if e.outcome == Outcome.HIT)
        total = len(bucket_evals)
        actual = hits / total
        expected = sum(e.confidence for e in bucket_evals) / total
        buckets.append(CalibrationBucket(
            confidence_range=(lo, min(hi, 1.0)),
            total=total,
            hits=hits,
            actual_hit_rate=actual,
            expected_confidence=expected,
            calibration_gap=actual - expected,
        ))

    return tuple(buckets)


def _build_directional(evals: list[SignalEvaluation]) -> tuple[DirectionalBreakdown, ...]:
    """
    소스별 BULLISH/BEARISH/NEUTRAL 적중률을 분석한다.
    핵심 질문: "하락 예측을 잘 하는가? 상승 예측을 잘 하는가?"
    """
    finished = [e for e in evals if e.outcome in (Outcome.HIT, Outcome.MISS)]
    sources = sorted({e.source for e in finished})
    results: list[DirectionalBreakdown] = []

    for src in sources:
        src_evals = [e for e in finished if e.source == src]

        def _dir_stats(direction: str) -> tuple[int, int, float]:
            d_evals = [e for e in src_evals if e.signal == direction]
            total = len(d_evals)
            hits = sum(1 for e in d_evals if e.outcome == Outcome.HIT)
            rate = hits / total if total > 0 else 0.0
            return total, hits, rate

        bt, bh, br = _dir_stats("BULLISH")
        bet, beh, ber = _dir_stats("BEARISH")
        nt, nh, nr = _dir_stats("NEUTRAL")

        counts = {"BULLISH": bt, "BEARISH": bet, "NEUTRAL": nt}
        dominant = max(counts, key=counts.get) if any(counts.values()) else "NEUTRAL"

        results.append(DirectionalBreakdown(
            source=src,
            bullish_total=bt, bullish_hits=bh, bullish_hit_rate=br,
            bearish_total=bet, bearish_hits=beh, bearish_hit_rate=ber,
            neutral_total=nt, neutral_hits=nh, neutral_hit_rate=nr,
            dominant_bias=dominant,
        ))

    return tuple(results)


def _build_market_contexts(
    evals: list[SignalEvaluation],
    raw_data: dict[str, dict],
) -> tuple[MarketContextMetrics, ...]:
    """
    시장 환경별 적중률을 분석한다.
    금리인하기, VIX 수준, 레짐별로 적중률이 어떻게 달라지는지.
    """
    consensus = [e for e in evals if e.source == "consensus"
                 and e.outcome in (Outcome.HIT, Outcome.MISS)]
    if not consensus or not raw_data:
        return ()

    contexts: list[MarketContextMetrics] = []

    # --- 금리 환경별 ---
    rate_easing: list[SignalEvaluation] = []
    rate_other: list[SignalEvaluation] = []
    for e in consensus:
        rd = raw_data.get(e.date, {})
        md = rd.get("market_data", {})
        fed = md.get("fed_rate", 0)
        # 금리인하기 판단: fed_rate < 4.5 (2024년 인하 시작 전 수준)
        if 0 < fed < 4.5:
            rate_easing.append(e)
        elif fed >= 4.5:
            rate_other.append(e)

    if rate_easing:
        contexts.append(_context_metrics("금리인하기 (FFR<4.5%)", rate_easing))
    if rate_other:
        contexts.append(_context_metrics("금리긴축/유지기 (FFR>=4.5%)", rate_other))

    # --- VIX 환경별 ---
    vix_low: list[SignalEvaluation] = []
    vix_mid: list[SignalEvaluation] = []
    vix_high: list[SignalEvaluation] = []
    for e in consensus:
        rd = raw_data.get(e.date, {})
        md = rd.get("market_data", {})
        vix = md.get("vix_current", 0)
        if vix > 0:
            if vix < 16:
                vix_low.append(e)
            elif vix < 22:
                vix_mid.append(e)
            else:
                vix_high.append(e)

    if vix_low:
        contexts.append(_context_metrics("VIX 안정 (<16)", vix_low))
    if vix_mid:
        contexts.append(_context_metrics("VIX 보통 (16-22)", vix_mid))
    if vix_high:
        contexts.append(_context_metrics("VIX 경계/극단 (>22)", vix_high))

    # --- 레짐별 ---
    regime_groups: dict[str, list[SignalEvaluation]] = {}
    for e in consensus:
        rd = raw_data.get(e.date, {})
        regime = rd.get("regime", {})
        regime_name = regime.get("regime", "") if regime else ""
        if regime_name:
            regime_groups.setdefault(regime_name, []).append(e)

    for regime_name, regime_evals in sorted(regime_groups.items()):
        contexts.append(_context_metrics(f"레짐: {regime_name}", regime_evals))

    return tuple(contexts)


def _context_metrics(label: str, evals: list[SignalEvaluation]) -> MarketContextMetrics:
    """시장 환경 메트릭 생성 헬퍼."""
    hits = sum(1 for e in evals if e.outcome == Outcome.HIT)
    total = len(evals)
    returns = [e.actual_return_pct for e in evals if e.actual_return_pct is not None]
    avg_ret = sum(returns) / len(returns) if returns else 0.0
    return MarketContextMetrics(
        context_label=label,
        total=total,
        hits=hits,
        hit_rate=hits / total if total > 0 else 0.0,
        avg_return=avg_ret,
    )


def _calculate_brier_score(evals: list[SignalEvaluation]) -> float:
    """
    Brier Score — 확률 예측의 교정 품질.
    0 = 완벽 교정, 1 = 최악.
    confidence를 적중 확률로 해석해 실제 결과(1=HIT, 0=MISS)와 비교.
    """
    consensus = [e for e in evals if e.source == "consensus"
                 and e.outcome in (Outcome.HIT, Outcome.MISS)]
    if not consensus:
        return 0.0

    total = 0.0
    for e in consensus:
        actual = 1.0 if e.outcome == Outcome.HIT else 0.0
        total += (e.confidence - actual) ** 2

    return total / len(consensus)


def _calculate_consecutive_misses(evals: list[SignalEvaluation]) -> int:
    """최근부터 역산해서 연속 MISS 횟수를 센다."""
    consensus = sorted(
        [e for e in evals if e.source == "consensus"
         and e.outcome in (Outcome.HIT, Outcome.MISS)],
        key=lambda e: e.date,
        reverse=True,
    )
    streak = 0
    for e in consensus:
        if e.outcome == Outcome.MISS:
            streak += 1
        else:
            break
    return streak


def _build_relative_performance(
    all_evals: list[SignalEvaluation],
) -> tuple[RelativePerformance, ...]:
    """
    US vs 국제 상대성과를 계산한다.
    EFA(선진국 ex-US), EEM(신흥국), DXY(달러)와 SPX를 비교.
    """
    try:
        import yfinance as yf
    except ImportError:
        return ()

    # 평가 기간 결정
    dates = sorted({e.date for e in all_evals})
    if not dates:
        return ()

    try:
        start_dt = datetime.strptime(dates[0], "%Y-%m-%d") - timedelta(days=10)
    except ValueError:
        return ()
    end_dt = datetime.now() + timedelta(days=1)

    # 확장 기간: 분기별 비교를 위해 1년 전부터
    extended_start = start_dt - timedelta(days=365)

    try:
        data = yf.download(
            ["^GSPC", "EFA", "EEM", "DX=F"],
            start=extended_start.strftime("%Y-%m-%d"),
            end=end_dt.strftime("%Y-%m-%d"),
            progress=False,
        )["Close"]
    except Exception as e:
        logger.warning(f"상대성과 데이터 다운로드 실패: {e}")
        return ()

    if data.empty:
        return ()

    results: list[RelativePerformance] = []

    def _period_return(ticker: str, start: str, end: str) -> float | None:
        if ticker not in data.columns:
            return None
        series = data[ticker].dropna()
        period = series[(series.index >= start) & (series.index <= end)]
        if len(period) < 2:
            return None
        return (float(period.iloc[-1]) - float(period.iloc[0])) / float(period.iloc[0]) * 100

    def _classify_regime(us_vs_efa: float, dxy_chg: float) -> str:
        """상대성과 레짐 분류."""
        if us_vs_efa > 3 and dxy_chg > 2:
            return "US 예외주의 (강달러+US 아웃퍼폼)"
        elif us_vs_efa > 3 and dxy_chg <= 2:
            return "US 아웃퍼폼 (달러 중립)"
        elif us_vs_efa < -3 and dxy_chg < -2:
            return "글로벌 리밸런싱 (약달러+US 언더퍼폼)"
        elif us_vs_efa < -3 and dxy_chg >= 0:
            return "US 언더퍼폼 (달러-주식 디커플링)"
        elif abs(us_vs_efa) <= 3:
            return "글로벌 동조"
        else:
            return "혼조"

    # 평가 데이터 기간 (스코어카드 커버 기간)
    eval_start = dates[0]
    eval_end = dates[-1]
    spx = _period_return("^GSPC", eval_start, eval_end)
    efa = _period_return("EFA", eval_start, eval_end)
    eem = _period_return("EEM", eval_start, eval_end)
    dxy = _period_return("DX=F", eval_start, eval_end)

    if all(v is not None for v in [spx, efa, eem, dxy]):
        us_efa = spx - efa
        us_eem = spx - eem
        results.append(RelativePerformance(
            period_label=f"스코어카드 기간 ({eval_start}~{eval_end})",
            spx_return=spx, efa_return=efa, eem_return=eem,
            dxy_change=dxy, us_vs_efa=us_efa, us_vs_eem=us_eem,
            regime_label=_classify_regime(us_efa, dxy),
        ))

    # 최근 분기별 비교 (최대 4분기)
    now = datetime.now()
    for q_offset in range(4):
        q_end_month = ((now.month - 1) - q_offset * 3) % 12 + 1
        q_end_year = now.year - ((now.month - 1 - q_offset * 3) < 0)
        if q_offset == 0:
            # 현재 분기는 진행 중
            q_start = datetime(q_end_year, q_end_month - (q_end_month - 1) % 3, 1)
            q_end_dt = now
            label = f"{q_end_year} Q{(q_end_month - 1) // 3 + 1} (진행 중)"
        else:
            q_num = (q_end_month - 1) // 3 + 1
            q_start = datetime(q_end_year, (q_num - 1) * 3 + 1, 1)
            # 분기 마지막 달
            q_last_month = q_num * 3
            if q_last_month == 12:
                q_end_dt = datetime(q_end_year, 12, 31)
            else:
                q_end_dt = datetime(q_end_year, q_last_month + 1, 1) - timedelta(days=1)
            label = f"{q_end_year} Q{q_num}"

        qs = q_start.strftime("%Y-%m-%d")
        qe = q_end_dt.strftime("%Y-%m-%d")

        spx_q = _period_return("^GSPC", qs, qe)
        efa_q = _period_return("EFA", qs, qe)
        eem_q = _period_return("EEM", qs, qe)
        dxy_q = _period_return("DX=F", qs, qe)

        if all(v is not None for v in [spx_q, efa_q, eem_q, dxy_q]):
            us_efa_q = spx_q - efa_q
            us_eem_q = spx_q - eem_q
            results.append(RelativePerformance(
                period_label=label,
                spx_return=spx_q, efa_return=efa_q, eem_return=eem_q,
                dxy_change=dxy_q, us_vs_efa=us_efa_q, us_vs_eem=us_eem_q,
                regime_label=_classify_regime(us_efa_q, dxy_q),
            ))

    return tuple(results)


def _build_narratives(
    relative_perf: tuple[RelativePerformance, ...],
    evaluated: list[SignalEvaluation],
    raw_data: dict[str, dict],
) -> tuple[NarrativeAssessment, ...]:
    """
    거시 내러티브(가설)를 데이터 기반으로 평가한다.
    """
    narratives: list[NarrativeAssessment] = []

    # --- 가설 1: 미국 예외주의 ---
    narratives.append(_assess_us_exceptionalism(relative_perf))

    # --- 가설 2: 금리인하 = 강세 ---
    narratives.append(_assess_rate_cut_bullish(evaluated, raw_data))

    # --- 가설 3: 달러-주식 동조 붕괴 ---
    if relative_perf:
        narratives.append(_assess_dxy_equity_decoupling(relative_perf))

    return tuple(n for n in narratives if n is not None)


def _assess_us_exceptionalism(
    relative_perf: tuple[RelativePerformance, ...],
) -> NarrativeAssessment:
    """미국 예외주의 가설 평가."""
    evidence: list[str] = []
    us_outperform_count = 0
    us_underperform_count = 0

    for rp in relative_perf:
        if "진행 중" in rp.period_label or "스코어카드" in rp.period_label:
            if rp.us_vs_efa > 3:
                evidence.append(f"{rp.period_label}: US 아웃퍼폼 (SPX-EFA={rp.us_vs_efa:+.1f}%p)")
                us_outperform_count += 1
            elif rp.us_vs_efa < -3:
                evidence.append(f"{rp.period_label}: US 언더퍼폼 (SPX-EFA={rp.us_vs_efa:+.1f}%p)")
                us_underperform_count += 1
            else:
                evidence.append(f"{rp.period_label}: 글로벌 동조 (SPX-EFA={rp.us_vs_efa:+.1f}%p)")

            if rp.dxy_change > 2:
                evidence.append(f"  달러 강세 (DXY {rp.dxy_change:+.1f}%) — 자본 유입 지속")
            elif rp.dxy_change < -2:
                evidence.append(f"  달러 약세 (DXY {rp.dxy_change:+.1f}%) — 자본 분산")
        else:
            # 과거 분기 추세
            if rp.us_vs_efa > 3:
                us_outperform_count += 1
            elif rp.us_vs_efa < -3:
                us_underperform_count += 1

    if not relative_perf:
        return NarrativeAssessment(
            hypothesis="미국 예외주의",
            verdict="불확실",
            evidence=("상대성과 데이터 없음",),
            signal_implication="판단 보류",
        )

    # 최근 추세 기반 판정
    recent = relative_perf[0] if relative_perf else None
    if recent and recent.us_vs_efa > 5:
        verdict = "지지"
        implication = (
            "SPX 중심 BULLISH 신호가 유효할 가능성 높음. "
            "단, 미국 예외주의 극단기에는 반전 리스크 주의"
        )
    elif recent and recent.us_vs_efa < -5:
        verdict = "약화"
        implication = (
            "US 언더퍼폼 구간 — SPX 기반 신호의 글로벌 대표성 약화. "
            "EFA/EEM 대비 상대약세가 시스템이 포착하지 못하는 리스크"
        )
    elif us_underperform_count > us_outperform_count:
        verdict = "약화"
        implication = (
            "최근 분기 US 언더퍼폼 우세 — 미국 예외주의 균열. "
            "BEARISH 신호 시 글로벌 자본 이동 방향 확인 필요"
        )
    else:
        verdict = "불확실"
        implication = "US vs 글로벌 격차 혼조 — 방향성 판단 보류"

    evidence.append(f"최근 4분기: US 아웃퍼폼 {us_outperform_count}회 / 언더퍼폼 {us_underperform_count}회")

    return NarrativeAssessment(
        hypothesis="미국 예외주의",
        verdict=verdict,
        evidence=tuple(evidence),
        signal_implication=implication,
    )


def _assess_rate_cut_bullish(
    evaluated: list[SignalEvaluation],
    raw_data: dict[str, dict],
) -> NarrativeAssessment:
    """'금리인하 = 강세' 가설 평가."""
    evidence: list[str] = []

    # 금리인하기 데이터 수집
    easing_evals = []
    for e in evaluated:
        if e.source != "consensus":
            continue
        rd = raw_data.get(e.date, {})
        fed = rd.get("market_data", {}).get("fed_rate", 0)
        if 0 < fed < 4.5:
            easing_evals.append(e)

    if not easing_evals:
        # PENDING 포함 — 금리 정보로 판단
        rates = []
        for date, rd in raw_data.items():
            fed = rd.get("market_data", {}).get("fed_rate", 0)
            if fed > 0:
                rates.append(fed)

        if rates:
            avg_rate = sum(rates) / len(rates)
            evidence.append(f"현재 FFR 평균 {avg_rate:.2f}% (인하 사이클 진행 중)")
            evidence.append("금리인하 시작 후 6-12개월 시차가 일반적 (Romer & Romer 2004)")
            evidence.append("현재 인하폭 약 190bp — 충분한 완화지만 시장은 아직 반응 혼조")

            # SPX 최근 추세로 판단
            all_returns = [e.actual_return_pct for e in evaluated
                          if e.source == "consensus" and e.actual_return_pct is not None]
            if all_returns:
                avg_ret = sum(all_returns) / len(all_returns)
                if avg_ret < -1:
                    evidence.append(f"평가 기간 평균 수익률 {avg_ret:+.1f}% — 인하에도 약세")
                    return NarrativeAssessment(
                        hypothesis="금리인하 = 강세",
                        verdict="반박",
                        evidence=tuple(evidence),
                        signal_implication=(
                            "금리인하만으로 BULLISH 편향 경계. "
                            "정책 불확실성(관세, 재정), 밸류에이션 부담이 완화 효과를 상쇄할 수 있음. "
                            "QuantAgent의 금리 가중치 재검토 필요"
                        ),
                    )

        return NarrativeAssessment(
            hypothesis="금리인하 = 강세",
            verdict="불확실",
            evidence=tuple(evidence) if evidence else ("평가 데이터 부족",),
            signal_implication="이력 축적 후 재평가 필요",
        )

    # 평가 완료 데이터가 있는 경우
    hits = sum(1 for e in easing_evals if e.outcome == Outcome.HIT)
    bullish_in_easing = [e for e in easing_evals if e.signal == "BULLISH"]
    bullish_hits = sum(1 for e in bullish_in_easing if e.outcome == Outcome.HIT)

    returns = [e.actual_return_pct for e in easing_evals if e.actual_return_pct is not None]
    avg_ret = sum(returns) / len(returns) if returns else 0

    evidence.append(f"금리인하기 합의 적중률: {hits}/{len(easing_evals)}")
    evidence.append(f"금리인하기 평균 실현 수익률: {avg_ret:+.2f}%")

    if bullish_in_easing:
        evidence.append(f"금리인하기 BULLISH 신호 적중: {bullish_hits}/{len(bullish_in_easing)}")

    if avg_ret > 1:
        verdict = "지지"
        implication = "금리인하 환경에서 실제 양의 수익률 확인 — 완화 효과 작동 중"
    elif avg_ret < -1:
        verdict = "반박"
        implication = (
            "금리인하에도 불구하고 음의 수익률 — 다른 역풍(관세, 지정학, 밸류에이션)이 "
            "완화 효과를 압도. 시스템이 금리에 과도한 가중치를 부여할 위험"
        )
    else:
        verdict = "불확실"
        implication = "금리인하 효과 미미 — 중립 구간"

    return NarrativeAssessment(
        hypothesis="금리인하 = 강세",
        verdict=verdict,
        evidence=tuple(evidence),
        signal_implication=implication,
    )


def _assess_dxy_equity_decoupling(
    relative_perf: tuple[RelativePerformance, ...],
) -> NarrativeAssessment | None:
    """달러-주식 동조 붕괴 가설 평가."""
    if not relative_perf:
        return None

    evidence: list[str] = []
    decoupled_count = 0

    for rp in relative_perf:
        # 전통적 상관: 달러 강세 → US 아웃퍼폼 (자본 유입)
        # 디커플링: 달러 강세인데 US 약세, 또는 달러 약세인데 US 강세
        traditional = (rp.dxy_change > 1 and rp.us_vs_efa > 0) or (rp.dxy_change < -1 and rp.us_vs_efa < 0)
        decoupled = (rp.dxy_change > 1 and rp.us_vs_efa < -2) or (rp.dxy_change < -1 and rp.us_vs_efa > 2)

        if decoupled:
            decoupled_count += 1
            evidence.append(
                f"{rp.period_label}: DXY {rp.dxy_change:+.1f}% but US-EFA {rp.us_vs_efa:+.1f}%p — 디커플링"
            )

    total = len(relative_perf)
    if total == 0:
        return None

    if decoupled_count >= 2:
        verdict = "지지"
        evidence.append(f"{decoupled_count}/{total} 기간에서 달러-주식 디커플링 관측")
        implication = (
            "달러 강세가 US 주식 강세를 의미하지 않는 구간 — "
            "DXY를 BULLISH 근거로 사용 시 주의. "
            "QuantAgent의 DXY 스코어링이 역방향으로 작용할 수 있음"
        )
    elif decoupled_count == 1:
        verdict = "불확실"
        evidence.append(f"{decoupled_count}/{total} 기간에서 디커플링 — 추세 확인 필요")
        implication = "단발성 디커플링 — 지속 여부 모니터링"
    else:
        verdict = "반박"
        evidence.append("달러-주식 전통적 상관 유지 중")
        implication = "DXY 기반 스코어링 신뢰 유지"

    return NarrativeAssessment(
        hypothesis="달러-주식 동조 붕괴",
        verdict=verdict,
        evidence=tuple(evidence),
        signal_implication=implication,
    )


def _build_warnings(
    diagnostics_data: dict,
    evals: list[SignalEvaluation],
    raw_data: dict[str, dict],
) -> tuple[str, ...]:
    """운용 경고 메시지를 생성한다."""
    warnings: list[str] = []

    # 연속 미스 경고
    streak = diagnostics_data.get("streak", 0)
    if streak >= 3:
        warnings.append(f"연속 {streak}회 MISS — 모델 drift 가능성. 입력 데이터/임계값 점검 필요")

    # 과신 경고
    for bucket in diagnostics_data.get("calibration", ()):
        if bucket.calibration_gap < -0.2 and bucket.total >= 3:
            lo, hi = bucket.confidence_range
            warnings.append(
                f"과신 감지: 신뢰도 {lo:.0%}-{hi:.0%} 구간에서 "
                f"실제 적중률 {bucket.actual_hit_rate:.0%} "
                f"(gap {bucket.calibration_gap:+.0%}p)"
            )

    # 방향 편향 경고
    for d in diagnostics_data.get("directional", ()):
        if d.source == "consensus":
            total = d.bullish_total + d.bearish_total + d.neutral_total
            if total >= 5:
                max_count = max(d.bullish_total, d.bearish_total, d.neutral_total)
                if max_count / total > 0.8:
                    warnings.append(
                        f"방향 편향: 합의 신호 {d.dominant_bias}가 {max_count}/{total}건 "
                        f"({max_count/total:.0%}) — 다양한 시장 환경 대응 점검 필요"
                    )

    # 금리인하기 특수 경고
    consensus_evals = [e for e in evals if e.source == "consensus"
                       and e.outcome in (Outcome.HIT, Outcome.MISS)]
    easing_bearish_miss = 0
    easing_total = 0
    for e in consensus_evals:
        rd = raw_data.get(e.date, {})
        fed = rd.get("market_data", {}).get("fed_rate", 0)
        if 0 < fed < 4.5:
            easing_total += 1
            if e.signal == "BEARISH" and e.outcome == Outcome.MISS:
                easing_bearish_miss += 1
    if easing_total >= 3 and easing_bearish_miss / easing_total > 0.5:
        warnings.append(
            "금리인하기 BEARISH 과잉: 완화 환경에서 약세 신호 미스 비율 높음 — "
            "금리인하의 시차 효과(6-12개월)를 반영하지 못할 수 있음"
        )

    # Brier score 경고
    brier = diagnostics_data.get("brier", 0.0)
    if brier > 0.3:
        warnings.append(f"Brier Score {brier:.3f} (>0.3) — 신뢰도 교정 품질 불량")

    # 데이터 부족 경고
    total_evaluated = len(consensus_evals)
    if total_evaluated < 10:
        warnings.append(
            f"평가 완료 {total_evaluated}건 — 통계적 유의성 부족 (최소 20건 이상 권장)"
        )

    return tuple(warnings)


def _build_diagnostics(
    evaluated: list[SignalEvaluation],
    all_evals: list[SignalEvaluation],
    raw_data: dict[str, dict],
) -> ScorecardDiagnostics:
    """전체 진단 분석을 수행한다."""
    calibration = _build_calibration(evaluated)
    directional = _build_directional(evaluated)
    market_contexts = _build_market_contexts(evaluated, raw_data)
    streak = _calculate_consecutive_misses(evaluated)
    brier = _calculate_brier_score(evaluated)

    # 상대성과 + 내러티브 (yfinance 호출)
    relative_perf = _build_relative_performance(all_evals)
    narratives = _build_narratives(relative_perf, evaluated, raw_data)

    warnings = _build_warnings(
        {"streak": streak, "calibration": calibration,
         "directional": directional, "brier": brier},
        evaluated,
        raw_data,
    )

    return ScorecardDiagnostics(
        calibration=calibration,
        directional=directional,
        market_contexts=market_contexts,
        consecutive_miss_streak=streak,
        brier_score=brier,
        warnings=warnings,
        relative_performance=relative_perf,
        narratives=narratives,
    )


def _build_diagnostics_pending(
    all_evals: list[SignalEvaluation],
    output_dir: str,
) -> ScorecardDiagnostics:
    """평가 완료 건이 없을 때의 진단 — 현재 상태 + 상대성과/내러티브 포함."""
    pending = [e for e in all_evals if e.source == "consensus" and e.outcome == Outcome.PENDING]
    warnings: list[str] = []
    raw_data: dict[str, dict] = {}

    if pending:
        signals = [e.signal for e in pending]
        from collections import Counter
        sig_counts = Counter(signals)
        warnings.append(
            f"PENDING {len(pending)}건: "
            f"{', '.join(f'{s} {c}건' for s, c in sig_counts.most_common())} "
            f"— 평가 대기 중"
        )

        avg_conf = sum(e.confidence for e in pending) / len(pending)
        warnings.append(f"대기 중 평균 신뢰도: {avg_conf:.0%}")

        raw_data = _load_raw_snapshots(output_dir, {e.date for e in pending})
        rates = []
        for e in pending:
            rd = raw_data.get(e.date, {})
            fed = rd.get("market_data", {}).get("fed_rate", 0)
            if fed > 0:
                rates.append(fed)
        if rates:
            avg_rate = sum(rates) / len(rates)
            warnings.append(
                f"현재 금리 환경: FFR 평균 {avg_rate:.2f}% (인하 사이클 중) — "
                "금리인하가 시장에 반영되는 시차(6-12개월)를 고려해야 함"
            )

    warnings.append("평가 완료 건 없음 — 이력이 쌓이면 자동으로 진단 생성됨")

    # 상대성과 + 내러티브는 평가 완료 없이도 계산 가능
    relative_perf = _build_relative_performance(all_evals)
    narratives = _build_narratives(relative_perf, all_evals, raw_data)

    return ScorecardDiagnostics(
        calibration=(),
        directional=(),
        market_contexts=(),
        consecutive_miss_streak=0,
        brier_score=0.0,
        warnings=tuple(warnings),
        relative_performance=relative_perf,
        narratives=narratives,
    )


# ============================================================================
# 설명 & 유틸
# ============================================================================

def _date_range(dates: set[str]) -> tuple[str, str]:
    sorted_dates = sorted(dates)
    return (sorted_dates[0], sorted_dates[-1]) if sorted_dates else ("", "")


def _build_explanation(
    consensus_metrics: SourceMetrics | None,
    agent_metrics: tuple[SourceMetrics, ...],
    total_evaluated: int,
    total_pending: int,
    horizon: int,
    best_agent: str,
    worst_agent: str,
    diagnostics: ScorecardDiagnostics | None = None,
) -> str:
    """요약 텍스트를 생성한다."""
    lines: list[str] = []

    if consensus_metrics:
        lines.append(
            f"합의 적중률 {consensus_metrics.hit_rate:.0%} "
            f"({consensus_metrics.hits}/{consensus_metrics.total}), "
            f"신뢰도 가중 {consensus_metrics.confidence_weighted_hit_rate:.0%}"
        )
    else:
        lines.append("합의 평가 데이터 없음")

    if agent_metrics:
        lines.append(f"최고: {best_agent} | 최저: {worst_agent}")

    lines.append(f"평가 기준: SPX {horizon}거래일 수익률")
    lines.append(f"평가 완료: {total_evaluated}건 | 대기: {total_pending}건")

    if diagnostics and diagnostics.brier_score > 0:
        lines.append(f"Brier Score: {diagnostics.brier_score:.3f} (낮을수록 교정 품질 양호)")

    if diagnostics and diagnostics.warnings:
        lines.append("")
        lines.append("[경고]")
        for w in diagnostics.warnings:
            lines.append(f"  - {w}")

    return "\n".join(lines)


def _empty_report(horizon: int) -> ScorecardReport:
    """이력 없을 때 빈 리포트."""
    return ScorecardReport(
        date_range=("", ""),
        horizon_days=horizon,
        total_evaluated=0,
        total_pending=0,
        consensus_metrics=None,
        agent_metrics=(),
        evaluations=(),
        best_agent="",
        worst_agent="",
        explanation="평가 가능한 이력이 없습니다.",
        diagnostics=None,
    )
