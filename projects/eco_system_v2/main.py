"""
main.py — eco_system_v2 CLI 진입점

사용법:
    python main.py --quick                          # AnalysisAgent만, ~30초
    python main.py --full                           # Analysis + Research + Quant → Debate, ~90초
    python main.py --forecast                       # full + ForecastAgent 추가
    python main.py --full --report                  # 실행 후 MD 리포트 생성
    python main.py --full --context "Fed pivot 가능성 높음"

    # 기업 타겟 분석 (job_assistant 연동)
    python main.py --quick --load-profile /path/to/analysis.json
    python main.py --quick --load-profile /path/to/analysis.json --portfolio
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (패키지 설치 없이 실행 가능)
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from infrastructure.collectors import collect_market, collect_extended_market, collect_fed_rate
from infrastructure.persistence import write, write_portfolio, compare_with_history
from infrastructure.profile_loader import load_profile
from agents.orchestrator import Orchestrator
from domain.market_data import MarketData

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="eco_system_v2 — 거시경제 멀티에이전트 분석 시스템"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true", help="AnalysisAgent만 실행 (~30s)")
    mode.add_argument("--full", action="store_true", help="Analysis+Research+Quant→Debate (~90s)")
    mode.add_argument("--forecast", action="store_true", help="full + ForecastAgent 추가")
    mode.add_argument("--scorecard", action="store_true", help="과거 신호 적중률 평가")
    parser.add_argument("--scorecard-horizon", type=int, default=None, help="스코어카드 평가 기간 (거래일, 기본 20)")
    parser.add_argument("--context", default="", help="추가 컨텍스트 (자유 텍스트)")
    parser.add_argument("--no-save", action="store_true", help="JSON 저장 건너뜀")
    parser.add_argument("--report", action="store_true", help="MD/HTML 리포트 생성")
    parser.add_argument(
        "--load-profile",
        metavar="PATH",
        default="",
        help="job_assistant Analysis JSON 경로 — 기업 타겟 분석 시 사용",
    )
    parser.add_argument(
        "--portfolio",
        action="store_true",
        help="--load-profile과 함께 사용 시 포트폴리오 마크다운 리포트 생성",
    )
    return parser.parse_args()


async def _run(args: argparse.Namespace) -> dict:
    quick = args.quick or (not args.full and not args.forecast)
    is_forecast = args.forecast

    # 0. 프로필 로드 (있을 경우)
    profile = None
    context = args.context
    if args.load_profile:
        profile = load_profile(args.load_profile)
        profile_context = profile.to_context()
        context = f"{profile_context}\n\n{context}".strip() if context else profile_context
        logger.info(f"[profile] {profile.company} / {profile.role} 컨텍스트 로드")

    # 1. 설정 검증
    config.validate(quick=quick)

    # 2. 데이터 수집 (Phase 1)
    logger.info("=== Phase 1: 데이터 수집 ===")
    market_base = collect_market()
    fed_rate = collect_fed_rate()

    # full/forecast 모드: 확장 데이터 수집 (레짐/리스크용)
    price_series = None
    vix_series = None
    extra_fields = {}
    if not quick:
        extended = collect_extended_market()
        price_series = extended.get("spx_prices", []) or None
        vix_series = extended.get("vix_prices", []) or None
        extra_fields = {
            "treasury_10y": extended.get("treasury_10y", 0.0),
            "treasury_2y": extended.get("treasury_2y", 0.0),
            "dxy_index": extended.get("dxy_index", 0.0),
            "gold_price": extended.get("gold_price", 0.0),
            "oil_price": extended.get("oil_price", 0.0),
            "copper_price": extended.get("copper_price", 0.0),
            "hyg_price": extended.get("hyg_price", 0.0),
        }

    market_data = MarketData(
        vix_current=market_base.vix_current,
        vix_30d_avg=market_base.vix_30d_avg,
        spx_return_30d=market_base.spx_return_30d,
        fed_rate=fed_rate,
        **extra_fields,
    )
    logger.info(f"수집 완료: {market_data.to_prompt_context()}")

    # 3. 에이전트 분석 (Phase 2)
    mode_name = "forecast" if is_forecast else ("quick" if quick else "full")
    logger.info(f"=== Phase 2: 분석 ({mode_name} 모드) ===")
    orchestrator = Orchestrator(
        anthropic_api_key=config.ANTHROPIC_API_KEY,
        perplexity_api_key=config.PERPLEXITY_API_KEY,
        claude_model=config.CLAUDE_MODEL,
        perplexity_model=config.PERPLEXITY_MODEL,
    )
    result = await orchestrator.run(
        market_data=market_data,
        context=context,
        quick=quick,
        forecast=is_forecast,
        price_series=price_series,
        vix_series=vix_series,
    )

    # 4. 결과 출력 (Phase 3)
    logger.info("=== Phase 3: 결과 ===")
    result_dict = result.to_dict()

    print("\n" + "=" * 60)
    if profile:
        print(f"대상       : {profile.company} | {profile.role}")
    print(f"모드       : {mode_name}")
    print(f"합의 신호  : {result_dict['consensus_signal']}")
    print(f"신뢰도     : {result_dict['consensus_confidence']:.0%}")
    print(f"근거       : {result_dict['consensus_rationale']}")
    if result.regime:
        print(f"레짐       : {result.regime.regime.value} (conf={result.regime.confidence:.0%})")
    if result.risk_metrics:
        print(f"리스크     : {result.risk_metrics.risk_level.value}")
    if result.lasso_forecast:
        lf = result.lasso_forecast
        print(f"LASSO 예측 : {lf.predicted_return:+.2f}% → {lf.signal.value} (R²={lf.r_squared:.3f})")
    if result.allocation:
        al = result.allocation
        alloc_str = " | ".join(f"{k} {v:.0f}%" for k, v in al.allocations)
        print(f"배분 추천  : {al.strategy_name} — {alloc_str}")
    if result.debate_summary:
        print(f"토론 요약  : {result.debate_summary[:150]}")

    # 합의 과정 상세 출력
    if result.consensus_breakdown:
        bd = result.consensus_breakdown
        print("-" * 60)
        print("[합의 과정]")
        print(bd.explanation)
    print("=" * 60 + "\n")

    # 5. 저장
    if not args.no_save:
        filepath = write(result_dict, config.OUTPUT_DIR)
        print(f"저장 완료: {filepath}")

        # 포트폴리오 리포트 (--portfolio 플래그 + 프로필이 있을 때)
        if args.portfolio and profile:
            portfolio_path = write_portfolio(
                result=result_dict,
                profile_dict=profile.to_dict(),
                output_dir=str(Path(config.OUTPUT_DIR) / "portfolio"),
            )
            print(f"포트폴리오: {portfolio_path}")

    # 6. 트렌드 비교 (과거 결과 대비)
    trend = compare_with_history(result_dict, config.OUTPUT_DIR)
    if trend:
        result_dict["trend"] = trend.to_dict()
        print("-" * 60)
        print("[트렌드 비교]")
        print(trend.explanation)
        print("-" * 60)

    # 7. 리포트 생성 (--report 플래그)
    if args.report:
        logger.info("=== Phase 4: 리포트 생성 ===")
        from infrastructure.report import generate_report, write_report

        report = await generate_report(
            result_dict=result_dict,
            api_key=config.ANTHROPIC_API_KEY,
            model=config.CLAUDE_MODEL,
        )
        report_path = write_report(report, config.OUTPUT_DIR, fmt="md")
        print(f"리포트: {report_path}")

        # HTML도 생성
        html_path = write_report(report, config.OUTPUT_DIR, fmt="html")
        print(f"리포트 (HTML): {html_path}")

    return result_dict


def _run_scorecard(args: argparse.Namespace) -> None:
    """스코어카드 실행 — asyncio 불필요."""
    from infrastructure.analysis.scorecard_service import evaluate_signals

    report = evaluate_signals(
        output_dir=config.OUTPUT_DIR,
        horizon_days=args.scorecard_horizon,
    )

    # 콘솔 출력
    print()
    print("=" * 70)
    print("SIGNAL ACCOUNTABILITY SCORECARD")
    if report.date_range[0]:
        print(f"기간: {report.date_range[0]} ~ {report.date_range[1]}")
    print(f"평가 기준: SPX {report.horizon_days} 거래일 수익률")
    print(f"평가 완료: {report.total_evaluated}건 | 대기: {report.total_pending}건")
    print("=" * 70)

    if report.consensus_metrics:
        cm = report.consensus_metrics
        print()
        print(f"[합의] 적중률 {cm.hit_rate:.0%} ({cm.hits}/{cm.total})")
        print(f"       신뢰도 가중 적중률: {cm.confidence_weighted_hit_rate:.0%}")

    if report.agent_metrics:
        print()
        print(f"{'에이전트':<12} {'적중률':>6} {'가중적중':>8} {'적중/전체':>9} {'적중신뢰':>8} {'미스신뢰':>8}")
        print("-" * 60)
        for m in report.agent_metrics:
            print(
                f"{m.source:<12} {m.hit_rate:>5.0%} {m.confidence_weighted_hit_rate:>7.0%} "
                f"{m.hits:>4}/{m.total:<4} {m.avg_confidence_when_hit:>7.0%} {m.avg_confidence_when_miss:>7.0%}"
            )

    if report.best_agent or report.worst_agent:
        print()
        print(f"최고: {report.best_agent} | 최저: {report.worst_agent}")

    # 진단 섹션
    diag = report.diagnostics
    if diag:
        # 교정 분석
        if diag.calibration:
            print()
            print("[교정 분석] 신뢰도 vs 실제 적중률")
            print(f"{'구간':<14} {'건수':>4} {'적중률':>6} {'기대치':>6} {'갭':>8}")
            print("-" * 44)
            for b in diag.calibration:
                lo, hi = b.confidence_range
                gap_str = f"{b.calibration_gap:+.0%}p"
                label = "과신" if b.calibration_gap < -0.1 else ("양호" if abs(b.calibration_gap) <= 0.1 else "과소신뢰")
                print(
                    f"{lo:.0%}-{hi:.0%}{'':>6} {b.total:>4} {b.actual_hit_rate:>5.0%} "
                    f"{b.expected_confidence:>5.0%} {gap_str:>7} {label}"
                )

        # 방향별 분석
        consensus_dir = [d for d in diag.directional if d.source == "consensus"]
        if consensus_dir:
            d = consensus_dir[0]
            print()
            print("[방향 비대칭]")
            if d.bullish_total:
                print(f"  BULLISH  적중 {d.bullish_hit_rate:.0%} ({d.bullish_hits}/{d.bullish_total})")
            if d.bearish_total:
                print(f"  BEARISH  적중 {d.bearish_hit_rate:.0%} ({d.bearish_hits}/{d.bearish_total})")
            if d.neutral_total:
                print(f"  NEUTRAL  적중 {d.neutral_hit_rate:.0%} ({d.neutral_hits}/{d.neutral_total})")
            print(f"  주요 편향: {d.dominant_bias}")

        # 시장 환경별
        if diag.market_contexts:
            print()
            print("[시장 환경별 적중률]")
            for mc in diag.market_contexts:
                print(
                    f"  {mc.context_label:<28} "
                    f"적중 {mc.hit_rate:.0%} ({mc.hits}/{mc.total}) "
                    f"평균수익 {mc.avg_return:+.2f}%"
                )

        # Brier Score
        if diag.brier_score > 0:
            print()
            quality = "양호" if diag.brier_score < 0.15 else ("보통" if diag.brier_score < 0.25 else "불량")
            print(f"[Brier Score] {diag.brier_score:.3f} ({quality})")

        # 상대성과
        if diag.relative_performance:
            print()
            print("[US vs 글로벌 상대성과]")
            print(f"{'기간':<32} {'SPX':>7} {'EFA':>7} {'EEM':>7} {'DXY':>7} {'US-EFA':>7}  레짐")
            print("-" * 90)
            for rp in diag.relative_performance:
                print(
                    f"{rp.period_label:<32} {rp.spx_return:>+6.1f}% {rp.efa_return:>+6.1f}% "
                    f"{rp.eem_return:>+6.1f}% {rp.dxy_change:>+6.1f}% {rp.us_vs_efa:>+6.1f}%  "
                    f"{rp.regime_label}"
                )

        # 내러티브 평가
        if diag.narratives:
            print()
            print("[거시 내러티브 평가]")
            for n in diag.narratives:
                verdict_mark = {"지지": "+", "약화": "~", "반박": "-", "불확실": "?"}.get(n.verdict, "?")
                print(f"  [{verdict_mark}] {n.hypothesis}: {n.verdict}")
                for ev in n.evidence:
                    print(f"      {ev}")
                print(f"      -> {n.signal_implication}")
                print()

        # 경고
        if diag.warnings:
            print("[경고]")
            for w in diag.warnings:
                print(f"  * {w}")

    print()
    print("=" * 70)
    print()

    # JSON 저장
    if not args.no_save:
        import json
        output_path = Path(config.OUTPUT_DIR)
        output_path.mkdir(parents=True, exist_ok=True)
        filepath = output_path / f"scorecard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"저장 완료: {filepath}")


def main() -> None:
    args = _parse_args()

    if args.scorecard:
        _run_scorecard(args)
        return

    if args.portfolio and not args.load_profile:
        print("ERROR: --portfolio는 --load-profile과 함께 사용해야 합니다.")
        sys.exit(1)

    result = asyncio.run(_run(args))

    # 비정상 신호 시 exit code 1 (CI/모니터링 연동용)
    if result.get("consensus_signal") == "BEARISH" and result.get("consensus_confidence", 0) > 0.7:
        sys.exit(1)


if __name__ == "__main__":
    main()
