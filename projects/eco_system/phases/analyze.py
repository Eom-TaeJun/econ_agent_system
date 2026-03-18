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

# ═══════════════════════════════════════════════════════════════
# 정량 임계값 기본값 및 근거
# ─────────────────────────────────────────────────────────────
# 프로필 YAML의 thresholds: 섹션으로 오버라이드 가능.
# 근거가 "경험적"인 항목은 히스토리컬 캘리브레이션으로 대체 권장.
# ═══════════════════════════════════════════════════════════════
DEFAULT_THRESHOLDS = {
    # ── 시그널 분류 ──────────────────────────────────────────
    # 섹터 ETF 30일 수익률 기준 BULLISH/BEARISH 경계 (%)
    # 근거: S&P 500 섹터 ETF 월간 수익률 σ ≈ 4-6%.
    #       ±2%는 약 0.4σ — "방향성이 보인다"는 최소 기준.
    #       ±1σ(±5%) 기준도 가능하나, 신호 빈도가 너무 낮아짐.
    "sector_signal_bull": 2.0,
    "sector_signal_bear": -2.0,

    # 팩터 ETF 시그널 경계 (%)
    # 근거: 팩터 ETF(MTUM, VLUE 등)는 롱온리라 섹터보다 분산 작음.
    #       월간 σ ≈ 3-4%. ±1%는 약 0.3σ — 팩터 로테이션 초기 감지용.
    "factor_signal_bull": 1.0,
    "factor_signal_bear": -1.0,

    # 크로스에셋 시그널 경계 (%)
    # 근거: 채권(TLT), 금(GLD), 달러(UUP)는 주식보다 월간 변동 작음.
    #       ±1%는 자산군 공통으로 적용 가능한 보수적 기준.
    "cross_asset_signal_bull": 1.0,
    "cross_asset_signal_bear": -1.0,

    # ── 레짐 확률 ────────────────────────────────────────────
    # VIX 임계값 (bull 조건)
    # 근거: CBOE VIX 1990-2024 중앙값 ≈ 17.5, 평균 ≈ 19.5.
    #       18 미만 = 중앙값 이하 = 시장 공포 낮음 (하위 ~50%).
    "regime_vix_bull": 18.0,

    # HY 스프레드 임계값 (bull 조건, %)
    # 근거: ICE BofA US HY OAS 1997-2024 중앙값 ≈ 4.5%.
    #       4% 미만 = 중앙값 이하 = 신용 환경 양호 (하위 ~40%).
    "regime_hy_bull": 4.0,

    # 수익률곡선 임계값 (bull 조건, %)
    # 근거: 10Y-2Y > 0 = 정상 기울기. 양수면 경기 확장 신호.
    #       Fed 연구(Estrella & Mishkin 1996): 역전 시 경기침체 확률 상승.
    "regime_yc_bull": 0.0,

    # SPX 30일 수익률 임계값 (bull 조건, %)
    # 근거: S&P 500 월평균 수익률 ≈ 0.7%, σ ≈ 4.5%.
    #       +2% ≈ 평균 + 0.3σ. 약한 양의 모멘텀도 bull 증거로 반영.
    "regime_spx_bull": 2.0,

    # 레짐 점수 가중치 — 합계 1.0
    # 근거: 경험적 배분. VIX(0.30)가 가장 높은 이유는
    #       실시간 내재변동성이 레짐 전환의 선행지표이기 때문 (Whaley 2009).
    #       나머지는 신용(0.25), 모멘텀(0.25), 금리구조(0.20) 순.
    # ⚠️ 백테스트 미수행 — 향후 히스토리컬 레짐 대비 정확도로 캘리브레이션 필요.
    "regime_weight_vix": 0.30,
    "regime_weight_hy": 0.25,
    "regime_weight_yc": 0.20,
    "regime_weight_spx": 0.25,

    # 베어 바닥 (1 - bull_score에서 추가 차감)
    # 근거: 최적 환경에서도 테일 리스크 ≥ 15%.
    #       S&P 500 월간 -5% 이상 하락 확률 ≈ 10-15% (1950-2024).
    "regime_bear_floor": 0.15,

    # 레짐 분류 경계
    # 근거: bull > 0.5 = 과반 이상이면 강세 레짐.
    #       bear > 0.35 = 비대칭 — 약세 시그널은 더 낮은 임계값으로 조기 감지.
    #       비대칭 이유: 하방 리스크의 비용이 상방 기회 놓침보다 크기 때문.
    "regime_dominant_bull": 0.50,
    "regime_dominant_bear": 0.35,

    # ── 폴백 기본값 (데이터 미수집 시) ───────────────────────
    # VIX 기본값: 장기 평균 ~19.5 → 20으로 반올림 (중립 가정)
    "fallback_vix": 20.0,
    # HY 스프레드 기본값: 장기 중앙값 ~4.5% → 4.0 (약간 낙관적 중립)
    "fallback_hy": 4.0,

    # ── 수익률곡선 형태 분류 ─────────────────────────────────
    # 근거: 10Y-2Y > 0.5% = 명확한 정상 기울기 (1990-2024 평균 ≈ 1.0%).
    #       < 0% = 역전 (Estrella & Mishkin 1996: 경기침체 선행).
    #       0~0.5% = 평탄화 구간 (전환기).
    "yc_normal": 0.50,
    "yc_inverted": 0.0,

    # ── 리스크 레벨 분류 ─────────────────────────────────────
    # VIX 고위험: > 25 ≈ 80th percentile (1990-2024)
    # VIX 저위험: < 15 ≈ 20th percentile
    "risk_vix_high": 25.0,
    "risk_vix_low": 15.0,
    # HY 고위험: > 6% ≈ 75th-80th percentile (1997-2024)
    # HY 저위험: < 3.5% ≈ 25th percentile
    "risk_hy_high": 6.0,
    "risk_hy_low": 3.5,
}


def _get_thresholds(profile: dict) -> dict:
    """프로필의 thresholds 섹션으로 기본값을 오버라이드."""
    t = dict(DEFAULT_THRESHOLDS)
    overrides = profile.get("thresholds", {})
    for k, v in overrides.items():
        if k in t:
            t[k] = float(v)
    return t

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

    모든 임계값은 DEFAULT_THRESHOLDS에서 가져오며,
    프로필 YAML의 thresholds: 섹션으로 오버라이드 가능.
    """
    sections = profile.get("report", {}).get("sections", [])
    t = _get_thresholds(profile)
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
                    "signal": (
                        "BULLISH" if ret > t["sector_signal_bull"]
                        else "BEARISH" if ret < t["sector_signal_bear"]
                        else "NEUTRAL"
                    ),
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
                    "signal": (
                        "BULLISH" if ret > t["factor_signal_bull"]
                        else "BEARISH" if ret < t["factor_signal_bear"]
                        else "NEUTRAL"
                    ),
                })
        extras["factor_signals"] = factor_signals

    # ── 레짐 확률 (regime_probability) ─────────────────────────
    if "regime_probability" in sections:
        vix = market_data.get("vixcls_current") or market_data.get("vix_current", t["fallback_vix"])
        hy = market_data.get("bamlh0a0hym2", t["fallback_hy"])
        yc = market_data.get("t10y2y", 0.0)
        spx_ret = market_data.get("gspc_return_30d") or market_data.get("spx_return_30d", 0)

        bull_score = 0.0
        if vix < t["regime_vix_bull"]:   bull_score += t["regime_weight_vix"]
        if hy < t["regime_hy_bull"]:     bull_score += t["regime_weight_hy"]
        if yc > t["regime_yc_bull"]:     bull_score += t["regime_weight_yc"]
        if spx_ret > t["regime_spx_bull"]: bull_score += t["regime_weight_spx"]
        bear_score = max(0.0, 1.0 - bull_score - t["regime_bear_floor"])
        riskoff_score = max(0.0, 1.0 - bull_score - bear_score)

        extras["regime_probability"] = {
            "bull": round(bull_score, 2),
            "bear": round(bear_score, 2),
            "risk_off": round(riskoff_score, 2),
            "dominant": (
                "BULL" if bull_score > t["regime_dominant_bull"]
                else "BEAR" if bear_score > t["regime_dominant_bear"]
                else "RISK-OFF"
            ),
            "inputs": {"vix": vix, "hy_spread": hy, "yield_curve": yc, "spx_ret_30d": spx_ret},
        }

    # ── 금리 커브 (yield_curve_view) ───────────────────────────
    if "yield_curve_view" in sections:
        dgs10 = market_data.get("dgs10", 0)
        dgs2 = market_data.get("dgs2", 0)
        t10y2y = market_data.get("t10y2y", 0)
        fedfunds = market_data.get("fedfunds", 0)

        shape = (
            "정상" if t10y2y > t["yc_normal"]
            else "역전" if t10y2y < t["yc_inverted"]
            else "평탄"
        )
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
                "HIGH" if vix > t["risk_vix_high"] or hy > t["risk_hy_high"]
                else "LOW" if vix < t["risk_vix_low"] and hy < t["risk_hy_low"]
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
                    "signal": (
                        "BULLISH" if ret > t["cross_asset_signal_bull"]
                        else "BEARISH" if ret < t["cross_asset_signal_bear"]
                        else "NEUTRAL"
                    ),
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
