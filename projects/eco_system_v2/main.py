"""
main.py — eco_system_v2 CLI 진입점

사용법:
    python main.py --quick                          # AnalysisAgent만, ~30초
    python main.py --full                           # Research + Analysis 병렬, ~60초
    python main.py --full --context "Fed pivot 가능성 높음"

    # 기업 타겟 분석 (job_assistant 연동)
    python main.py --quick --load-profile /path/to/웨이브릿지_퀀트리서처_2026-02-26_analysis.json
    python main.py --quick --load-profile /path/to/analysis.json --portfolio
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (패키지 설치 없이 실행 가능)
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from infrastructure.collectors import collect_market, collect_fed_rate
from infrastructure.persistence import write, write_portfolio
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
    mode.add_argument("--full", action="store_true", help="Research + Analysis 병렬 (~60s)")
    parser.add_argument("--context", default="", help="추가 컨텍스트 (자유 텍스트)")
    parser.add_argument("--no-save", action="store_true", help="JSON 저장 건너뜀")
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
    quick = args.quick or (not args.full)  # 기본값은 quick

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
    market_data = MarketData(
        vix_current=market_base.vix_current,
        vix_30d_avg=market_base.vix_30d_avg,
        spx_return_30d=market_base.spx_return_30d,
        fed_rate=fed_rate,
    )
    logger.info(f"수집 완료: {market_data.to_prompt_context()}")

    # 3. 에이전트 분석 (Phase 2)
    logger.info(f"=== Phase 2: 분석 ({'quick' if quick else 'full'} 모드) ===")
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
    )

    # 4. 결과 출력 (Phase 3)
    logger.info("=== Phase 3: 결과 ===")
    result_dict = result.to_dict()

    print("\n" + "=" * 50)
    if profile:
        print(f"대상     : {profile.company} | {profile.role}")
    print(f"합의 신호  : {result_dict['consensus_signal']}")
    print(f"신뢰도     : {result_dict['consensus_confidence']:.0%}")
    print(f"근거       : {result_dict['consensus_rationale']}")
    print("=" * 50 + "\n")

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

    return result_dict


def main() -> None:
    args = _parse_args()

    if args.portfolio and not args.load_profile:
        print("ERROR: --portfolio는 --load-profile과 함께 사용해야 합니다.")
        sys.exit(1)

    result = asyncio.run(_run(args))

    # 비정상 신호 시 exit code 1 (CI/모니터링 연동용)
    if result.get("consensus_signal") == "BEARISH" and result.get("consensus_confidence", 0) > 0.7:
        sys.exit(1)


if __name__ == "__main__":
    main()
