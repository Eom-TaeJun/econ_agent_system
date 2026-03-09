"""
eco_system Phase 2: 분석
프로필 기반으로 에이전트 구성, task/context, 토론 설정을 동적으로 결정
"""

import asyncio
import logging

from agents.orchestrator import Orchestrator
from agents.analysis import AnalysisAgent
from agents.research import ResearchAgent
from core.schemas import EcoResult

logger = logging.getLogger(__name__)

# 프로필 focus → task 문구 매핑
FOCUS_TASK_MAP = {
    "sector_rotation":    "섹터 로테이션과 스타일 팩터(성장/가치) 전환 신호 분석",
    "earnings_momentum":  "어닝 모멘텀과 컨센서스 대비 서프라이즈 방향 판단",
    "macro_regime":       "글로벌 거시경제 레짐 분류 (bull/bear/risk-off) 및 전환 신호",
    "credit_spread":      "신용 스프레드 방향과 유동성 환경 분석",
    "factor_rotation":    "팩터 로테이션 (value/momentum/quality/low-vol) 신호",
    "inflation_regime":   "인플레이션 레짐 (상승/둔화/디플레) 및 통화정책 영향",
    "valuation":          "밸류에이션 멀티플과 금리 환경 간 괴리 분석",
    "momentum":           "크로스에셋 모멘텀 신호 및 추세 강도",
    "risk_on_off":        "리스크온/오프 전환 신호와 안전자산 수요",
    "policy_outlook":     "연준·ECB 정책 경로와 시장 기대 괴리",
}


def _build_task(profile: dict) -> str:
    """프로필의 analysis.focus 목록으로 task 문장 생성."""
    focus_list = profile.get("analysis", {}).get("focus", [])
    if not focus_list:
        return "현재 글로벌 거시경제 상황 분석 및 투자 신호 판단"
    items = [FOCUS_TASK_MAP.get(f, f) for f in focus_list[:3]]  # 상위 3개만
    return " / ".join(items)


def _build_context(market_data: dict, profile: dict) -> str:
    """수집 데이터 요약 + 프로필 분석 지시사항."""
    lines = [f"수집 데이터 키: {list(market_data.keys())[:15]}"]
    overlay = profile.get("agents", {}).get("system_prompt_overlay", "")
    if overlay:
        lines.append(f"\n[직무별 분석 지침]\n{overlay.strip()}")
    return "\n".join(lines)


def analyze(market_data: dict, profile: dict | None = None) -> EcoResult:
    """
    프로필 기반 에이전트 분석.
    - agents.research / agents.analysis 플래그로 에이전트 구성
    - analysis.mode로 quick/full 결정
    - agents.debate 설정으로 토론 제어
    """
    if profile is None:
        profile = {}

    agents_cfg = profile.get("agents", {})
    mode = profile.get("analysis", {}).get("mode", "quick")

    # 에이전트 구성
    spokes = []
    if agents_cfg.get("research", True) and mode == "full":
        spokes.append(ResearchAgent())
    spokes.append(AnalysisAgent())

    # 토론 설정 오버라이드
    debate_cfg = agents_cfg.get("debate", {})
    orchestrator = Orchestrator()
    orchestrator.spokes = spokes
    if debate_cfg:
        orchestrator.max_rounds = debate_cfg.get("max_rounds", 2)
        orchestrator.consensus_threshold = debate_cfg.get("consensus_threshold", 0.80)

    task = _build_task(profile)
    context = _build_context(market_data, profile)

    logger.info(f"[analyze] 모드={mode} | 에이전트={[s.name for s in spokes]} | task={task[:60]}")
    return asyncio.run(orchestrator.run(task=task, data=market_data, context=context))
