#!/usr/bin/env python3
"""
eco_system — 경량 경제 인텔리전스 에이전트
사용법:
    python main.py --quick                  # 빠른 분석 (기본 프로필)
    python main.py --full                   # 전체 분석 (AI 토론)
    python main.py --profile ra_equity      # 해외주식 RA 모드
    python main.py --profile quant --full   # 퀀트 + 전체 분석
    python main.py --profile macro          # 매크로 모드
    python main.py --list-profiles          # 사용 가능한 프로필 목록
"""

import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from core.profile import load_profile, list_profiles
from phases.collect import collect
from phases.analyze import analyze
from phases.report import report


def main():
    parser = argparse.ArgumentParser(description="eco_system 경제 분석")
    parser.add_argument(
        "--profile", default="base",
        help="직무 프로필 (ra_equity | quant | macro | base)"
    )
    parser.add_argument("--list-profiles", action="store_true", help="프로필 목록 출력")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--quick", action="store_true", help="빠른 분석 (프로필 기본값 오버라이드)")
    group.add_argument("--full", action="store_true", help="전체 분석 (프로필 기본값 오버라이드)")
    args = parser.parse_args()

    if args.list_profiles:
        list_profiles()
        return

    # 프로필 로드
    profile = load_profile(args.profile)

    # --quick / --full 플래그가 있으면 프로필 기본값 오버라이드
    if args.quick:
        profile["analysis"]["mode"] = "quick"
    elif args.full:
        profile["analysis"]["mode"] = "full"

    mode = profile["analysis"]["mode"]
    profile_name = profile.get("_profile_name", "base")

    print(f"\n[eco_system] 프로필: {profile_name.upper()} | 모드: {mode.upper()}")

    # Phase 1: 수집
    print("[Phase 1] 데이터 수집...")
    market_data = collect(profile=profile)

    # Phase 2: 분석
    print(f"[Phase 2] 에이전트 분석 ({mode})...")
    result = analyze(market_data, profile=profile)

    # Phase 3: 결과
    print("[Phase 3] 결과 저장...")
    report(result, profile=profile)


if __name__ == "__main__":
    main()
