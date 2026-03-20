"""
experimental/gfsi/cli.py — GFSI CLI 진입점

사용법:
  # 일일 수집 + 산출 + 저장
  python -m experimental.gfsi.cli

  # 선행성 분석 포함
  python -m experimental.gfsi.cli --analyze

  # 과거 기록 리포트만
  python -m experimental.gfsi.cli --report-only

  # dry-run (수집만, 저장 안 함)
  python -m experimental.gfsi.cli --dry-run

  # 전체 산출 과정 추적 (explain)
  python -m experimental.gfsi.cli --explain
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from .calculator import calculate_gfsi
from .collector import collect_all
from .evaluator import (
    analyze_lead_lag,
    compute_daily_eval,
    generate_report,
    load_history,
    save_daily,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("gfsi")


def main() -> None:
    parser = argparse.ArgumentParser(description="GFSI — Global Fear & Stress Index")
    parser.add_argument("--analyze", action="store_true", help="선행/후행 분석 포함")
    parser.add_argument("--report-only", action="store_true", help="과거 기록 리포트만 출력")
    parser.add_argument("--dry-run", action="store_true", help="수집만, 저장 안 함")
    parser.add_argument("--explain", action="store_true", help="전체 산출 과정 추적")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    fred_key = os.environ.get("FRED_API_KEY")

    if args.report_only:
        _report_only(args.analyze)
        return

    # Phase 1: 데이터 수집
    logger.info("Phase 1: Collecting data...")
    raw_data = collect_all(fred_api_key=fred_key)

    # Phase 2: GFSI 산출
    logger.info("Phase 2: Calculating GFSI...")
    result = calculate_gfsi(raw_data)

    # Phase 3: 저장
    if not args.dry_run:
        path = save_daily(result, raw_data)
        logger.info("Saved to %s", path)

    # Phase 4: 평가
    history = load_history()
    evaluation = compute_daily_eval(result, history)

    lead_lag = None
    if args.analyze:
        logger.info("Phase 4: Lead-lag analysis...")
        lead_lag = analyze_lead_lag(history)

    # 출력
    if args.explain:
        from .explainer import explain_gfsi
        print(explain_gfsi(raw_data, result))
    elif args.json:
        output = {
            "evaluation": evaluation.to_dict(),
        }
        if lead_lag:
            output["lead_lag"] = [ll.to_dict() for ll in lead_lag]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        report = generate_report(evaluation, lead_lag)
        print(report)
        print(result.to_summary())


def _report_only(analyze: bool) -> None:
    """과거 기록만으로 리포트 생성."""
    history = load_history(days=60)
    if not history:
        print("No history data found.")
        sys.exit(1)

    latest = history[-1]
    from .domain import GFSIResult, ChannelScore, Channel, classify_level

    # 마지막 기록 재구성 (v0.1 옛 채널명 호환)
    r = latest.get("result", {})
    valid_channels = {c.value for c in Channel}
    channels = tuple(
        ChannelScore(
            channel=Channel(ch["channel"]),
            score=ch["score"],
            raw_values=ch.get("raw_values", {}),
            signal=ch.get("signal", ""),
            data_quality=ch.get("data_quality", 1.0),
        )
        for ch in r.get("channels", [])
        if ch.get("channel") in valid_channels
    )
    result = GFSIResult(
        score=r.get("gfsi_score", 50.0),
        level=classify_level(r.get("gfsi_score", 50.0)),
        channels=channels,
        vix_current=r.get("vix_current", 0.0),
        collected_at=r.get("collected_at", ""),
    )

    evaluation = compute_daily_eval(result, history[:-1])

    lead_lag = None
    if analyze and len(history) >= 20:
        lead_lag = analyze_lead_lag(history)

    report = generate_report(evaluation, lead_lag)
    print(report)

    # 기간 요약
    if len(history) >= 2:
        scores = [h["result"]["gfsi_score"] for h in history if "result" in h]
        print(f"\n## {len(history)}일 기록 요약")
        print(f"평균: {sum(scores)/len(scores):.1f} | "
              f"최저: {min(scores):.1f} | 최고: {max(scores):.1f}")


if __name__ == "__main__":
    main()
