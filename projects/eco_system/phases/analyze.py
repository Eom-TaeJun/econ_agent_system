"""
eco_system Phase 2: 분석
- 프로필 기반 에이전트 구성, task/context 동적 생성
- 섹션별 정량 데이터(sector_signals, regime, yield_curve 등) 계산 → EcoResult.extras
"""

import asyncio
import logging

from agents.orchestrator import Orchestrator
from agents.analysis import AnalysisAgent
from agents.research import ResearchAgent
from core.schemas import EcoResult

logger = logging.getLogger(__name__)

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

# 섹터 ETF → 이름 매핑
SECTOR_NAMES = {
    "xlk": "테크", "xlf": "금융", "xle": "에너지", "xlv": "헬스케어",
    "xlc": "커뮤니케이션", "xli": "산업재", "xlp": "필수소비재",
    "xlu": "유틸리티", "xlb": "소재", "xlre": "리츠",
}

# 팩터 ETF → 이름 매핑
FACTOR_NAMES = {
    "mtum": "모멘텀", "vlue": "밸류", "qual": "퀄리티",
    "usmv": "저변동성", "size": "소형주",
}


def _build_task(profile: dict) -> str:
    focus_list = profile.get("analysis", {}).get("focus", [])
    if not focus_list:
        return "현재 글로벌 거시경제 상황 분석 및 투자 신호 판단"
    items = [FOCUS_TASK_MAP.get(f, f) for f in focus_list[:3]]
    return " / ".join(items)


def _build_context(market_data: dict, profile: dict) -> str:
    lines = [f"수집 데이터 키: {list(market_data.keys())[:15]}"]
    overlay = profile.get("agents", {}).get("system_prompt_overlay", "")
    if overlay:
        lines.append(f"\n[직무별 분석 지침]\n{overlay.strip()}")
    return "\n".join(lines)


def _compute_extras(market_data: dict, profile: dict) -> dict:
    """
    profile의 report.sections에 맞춰 정량 데이터를 미리 계산.
    계산된 데이터는 EcoResult.extras에 저장되어 report.py에서 렌더링됨.
    """
    sections = profile.get("report", {}).get("sections", [])
    extras: dict = {}

    # ── 섹터 분석 (sector_breakdown) ───────────────────────────
    if "sector_breakdown" in sections:
        sector_signals = []
        for key, name in SECTOR_NAMES.items():
            ret = market_data.get(f"{key}_return_30d")
            cur = market_data.get(f"{key}_current")
            if ret is not None:
                sector_signals.append({
                    "ticker": key.upper(),
                    "name": name,
                    "return_30d": round(ret, 2),
                    "current": round(cur, 2) if cur else None,
                    "signal": "BULLISH" if ret > 2 else ("BEARISH" if ret < -2 else "NEUTRAL"),
                })
        sector_signals.sort(key=lambda x: x["return_30d"], reverse=True)
        extras["sector_signals"] = sector_signals

    # ── 팩터 노출도 (factor_exposure) ──────────────────────────
    if "factor_exposure" in sections:
        factor_signals = []
        for key, name in FACTOR_NAMES.items():
            ret = market_data.get(f"{key}_return_30d")
            if ret is not None:
                factor_signals.append({
                    "ticker": key.upper(),
                    "name": name,
                    "return_30d": round(ret, 2),
                    "signal": "BULLISH" if ret > 1 else ("BEARISH" if ret < -1 else "NEUTRAL"),
                })
        extras["factor_signals"] = factor_signals

    # ── 레짐 확률 (regime_probability) ─────────────────────────
    if "regime_probability" in sections:
        vix = market_data.get("vixcls_current") or market_data.get("vix_current", 20)
        hy = market_data.get("bamlh0a0hym2", 4.0)
        yc = market_data.get("t10y2y", 0.0)
        spx_ret = market_data.get("gspc_return_30d") or market_data.get("spx_return_30d", 0)

        # 단순 규칙 기반 레짐 확률
        bull_score = 0.0
        if vix < 18:     bull_score += 0.30
        if hy < 4.0:     bull_score += 0.25
        if yc > 0:       bull_score += 0.20
        if spx_ret > 2:  bull_score += 0.25
        bear_score = max(0.0, 1.0 - bull_score - 0.15)
        riskoff_score = max(0.0, 1.0 - bull_score - bear_score)

        extras["regime_probability"] = {
            "bull": round(bull_score, 2),
            "bear": round(bear_score, 2),
            "risk_off": round(riskoff_score, 2),
            "dominant": "BULL" if bull_score > 0.5 else ("BEAR" if bear_score > 0.35 else "RISK-OFF"),
            "inputs": {"vix": vix, "hy_spread": hy, "yield_curve": yc, "spx_ret_30d": spx_ret},
        }

    # ── 금리 커브 (yield_curve_view) ───────────────────────────
    if "yield_curve_view" in sections:
        dgs10 = market_data.get("dgs10", 0)
        dgs2 = market_data.get("dgs2", 0)
        t10y2y = market_data.get("t10y2y", 0)
        fedfunds = market_data.get("fedfunds", 0)

        shape = "정상" if t10y2y > 0.5 else ("역전" if t10y2y < 0 else "평탄")
        extras["yield_curve"] = {
            "fed_funds": fedfunds,
            "2y": dgs2,
            "10y": dgs10,
            "spread_10y2y": round(t10y2y, 3),
            "shape": shape,
            "view": f"10Y-2Y 스프레드 {t10y2y:.2f}% → 커브 {shape}",
        }

    # ── 리스크 지표 (risk_metrics) ──────────────────────────────
    if "risk_metrics" in sections:
        vix = market_data.get("vixcls_current") or market_data.get("vix_current", 0)
        hy = market_data.get("bamlh0a0hym2", 0)
        ig = market_data.get("bamlc0a0cm", 0)
        extras["risk_metrics"] = {
            "vix": vix,
            "hy_spread_pct": hy,
            "ig_spread_pct": ig,
            "risk_level": (
                "HIGH" if vix > 25 or hy > 6
                else "LOW" if vix < 15 and hy < 3.5
                else "MEDIUM"
            ),
        }

    # ── 크로스에셋 매트릭스 (cross_asset_matrix) ───────────────
    if "cross_asset_matrix" in sections:
        assets = {
            "미국주식(SPY)": market_data.get("spy_return_30d"),
            "채권(TLT)":    market_data.get("tlt_return_30d"),
            "금(GLD)":      market_data.get("gld_return_30d"),
            "하이일드(HYG)": market_data.get("hyg_return_30d"),
            "달러(UUP)":    market_data.get("uup_return_30d"),
        }
        matrix = []
        for name, ret in assets.items():
            if ret is not None:
                matrix.append({
                    "asset": name,
                    "return_30d": round(ret, 2),
                    "signal": "BULLISH" if ret > 1 else ("BEARISH" if ret < -1 else "NEUTRAL"),
                })
        extras["cross_asset_matrix"] = matrix

    return extras


def analyze(market_data: dict, profile: dict | None = None) -> EcoResult:
    """프로필 기반 에이전트 분석 + 섹션 데이터 계산."""
    if profile is None:
        profile = {}

    agents_cfg = profile.get("agents", {})
    mode = profile.get("analysis", {}).get("mode", "quick")

    # 에이전트 구성
    spokes = []
    if agents_cfg.get("research", True) and mode == "full":
        spokes.append(ResearchAgent())
    spokes.append(AnalysisAgent())

    orchestrator = Orchestrator()
    orchestrator.spokes = spokes
    orchestrator.use_guardrail = agents_cfg.get("guardrail", False) and mode == "full"

    debate_cfg = agents_cfg.get("debate", {})
    if debate_cfg:
        orchestrator.max_rounds = debate_cfg.get("max_rounds", 2)
        orchestrator.consensus_threshold = debate_cfg.get("consensus_threshold", 0.80)

    task = _build_task(profile)
    context = _build_context(market_data, profile)

    logger.info(
        f"[analyze] 모드={mode} | 에이전트={[s.name for s in spokes]} "
        f"| guardrail={orchestrator.use_guardrail}"
    )

    result = asyncio.run(orchestrator.run(task=task, data=market_data, context=context))

    # 섹션별 정량 데이터 계산
    result.extras = _compute_extras(market_data, profile)

    return result
