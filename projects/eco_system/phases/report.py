"""
eco_system Phase 3: 결과 저장 및 출력
프로필의 report.sections 목록에 따라 필요한 섹션만 렌더링
"""

import json
import os
from core.schemas import EcoResult

SIGNAL_EMOJI = {"BULLISH": "📈", "NEUTRAL": "➡️", "BEARISH": "📉"}
SIGNAL_KO    = {"BULLISH": "강세",  "NEUTRAL": "중립",  "BEARISH": "약세"}


# ── 섹션 렌더러 ────────────────────────────────────────────────

def _render_signal(r: EcoResult, _) -> str:
    e = SIGNAL_EMOJI.get(r.consensus_signal.value, "❓")
    k = SIGNAL_KO.get(r.consensus_signal.value, "")
    return f"  신호: {e} {r.consensus_signal.value} ({k})"

def _render_confidence(r: EcoResult, _) -> str:
    bar = "█" * int(r.consensus_confidence * 10) + "░" * (10 - int(r.consensus_confidence * 10))
    return f"  신뢰도: {bar} {r.consensus_confidence:.0%}"

def _render_rationale(r: EcoResult, _) -> str:
    return f"  근거: {r.summary}"

def _render_key_factors(r: EcoResult, _) -> str:
    if not r.key_factors:
        return ""
    items = "\n".join(f"    • {f}" for f in r.key_factors)
    return f"  핵심 요인:\n{items}"

def _render_guardrail(r: EcoResult, _) -> str:
    if not r.guardrail_notes:
        return ""
    return f"  [검증] {r.guardrail_notes}"

def _render_sector_breakdown(r: EcoResult, _) -> str:
    sectors = r.extras.get("sector_signals", [])
    if not sectors:
        return "  [섹터 분석]: 데이터 없음 (sector ETF 티커를 프로필에 추가하세요)"
    lines = ["  [섹터 분석] 30일 수익률 (상위→하위):"]
    for s in sectors:
        e = SIGNAL_EMOJI.get(s["signal"], "➡️")
        lines.append(f"    {e} {s['ticker']:6s} {s['name']:8s} {s['return_30d']:+.1f}%")
    return "\n".join(lines)

def _render_top_picks(r: EcoResult, _) -> str:
    sectors = r.extras.get("sector_signals", [])
    if not sectors:
        return ""
    bullish = [s for s in sectors if s["signal"] == "BULLISH"]
    bearish = [s for s in sectors if s["signal"] == "BEARISH"]
    lines = ["  [Top Picks]"]
    if bullish:
        names = ", ".join(f"{s['name']}({s['return_30d']:+.1f}%)" for s in bullish[:3])
        lines.append(f"    비중확대 후보: {names}")
    if bearish:
        names = ", ".join(f"{s['name']}({s['return_30d']:+.1f}%)" for s in bearish[:2])
        lines.append(f"    비중축소 후보: {names}")
    return "\n".join(lines)

def _render_risk_factors(r: EcoResult, _) -> str:
    risk = r.extras.get("risk_metrics", {})
    if not risk:
        return ""
    level = risk.get("risk_level", "N/A")
    vix = risk.get("vix", 0)
    hy = risk.get("hy_spread_pct", 0)
    return (
        f"  [리스크] 레벨={level} | VIX={vix:.1f} | "
        f"HY스프레드={hy:.2f}% | IG스프레드={risk.get('ig_spread_pct', 0):.2f}%"
    )

def _render_factor_exposure(r: EcoResult, _) -> str:
    factors = r.extras.get("factor_signals", [])
    if not factors:
        return "  [팩터 노출도]: 데이터 없음 (factor ETF 티커를 프로필에 추가하세요)"
    lines = ["  [팩터 노출도] 30일 수익률:"]
    for f in sorted(factors, key=lambda x: x["return_30d"], reverse=True):
        e = SIGNAL_EMOJI.get(f["signal"], "➡️")
        lines.append(f"    {e} {f['ticker']:6s} {f['name']:8s} {f['return_30d']:+.1f}%")
    return "\n".join(lines)

def _render_regime_probability(r: EcoResult, _) -> str:
    reg = r.extras.get("regime_probability", {})
    if not reg:
        return "  [레짐 확률]: 계산 실패"
    bull = int(reg.get("bull", 0) * 100)
    bear = int(reg.get("bear", 0) * 100)
    roff = int(reg.get("risk_off", 0) * 100)
    dom  = reg.get("dominant", "N/A")
    return (
        f"  [레짐 확률] 강세={bull}% | 약세={bear}% | 리스크오프={roff}% "
        f"→ 우세: {dom}"
    )

def _render_risk_metrics(r: EcoResult, _) -> str:
    return _render_risk_factors(r, _)  # 동일 데이터 재사용

def _render_lasso_coefficients(r: EcoResult, _) -> str:
    # LASSO는 별도 구현 필요 — 현재는 regime 데이터로 대체
    reg = r.extras.get("regime_probability", {})
    if reg:
        inputs = reg.get("inputs", {})
        lines = ["  [LASSO 주요 입력변수]"]
        for k, v in inputs.items():
            lines.append(f"    {k}: {v:.2f}" if isinstance(v, float) else f"    {k}: {v}")
        return "\n".join(lines)
    return "  [LASSO 계수]: full 모드에서 계산됩니다"

def _render_yield_curve_view(r: EcoResult, _) -> str:
    yc = r.extras.get("yield_curve", {})
    if not yc:
        return "  [금리 커브]: FRED 데이터 없음 (FRED_API_KEY 설정 필요)"
    return (
        f"  [금리 커브] {yc.get('view', '')} | "
        f"FF={yc.get('fed_funds', 0):.2f}% | "
        f"2Y={yc.get('2y', 0):.2f}% | 10Y={yc.get('10y', 0):.2f}%"
    )

def _render_policy_outlook(r: EcoResult, _) -> str:
    # ResearchAgent의 rationale에서 도출 (full 모드)
    for resp in r.agent_responses:
        if resp.agent == "research":
            return f"  [통화정책 전망] {resp.rationale[:120]}"
    yc = r.extras.get("yield_curve", {})
    ff = yc.get("fed_funds", 0)
    return f"  [통화정책] 현재 기준금리 {ff:.2f}% (ResearchAgent 미실행)"

def _render_cross_asset_matrix(r: EcoResult, _) -> str:
    matrix = r.extras.get("cross_asset_matrix", [])
    if not matrix:
        return "  [크로스에셋]: 데이터 없음"
    lines = ["  [크로스에셋 매트릭스] 30일 수익률:"]
    for item in matrix:
        e = SIGNAL_EMOJI.get(item["signal"], "➡️")
        lines.append(f"    {e} {item['asset']:15s} {item['return_30d']:+.1f}%")
    return "\n".join(lines)


SECTION_RENDERERS = {
    "signal":               _render_signal,
    "confidence":           _render_confidence,
    "rationale":            _render_rationale,
    "key_factors":          _render_key_factors,
    "guardrail_notes":      _render_guardrail,
    "sector_breakdown":     _render_sector_breakdown,
    "top_picks":            _render_top_picks,
    "risk_factors":         _render_risk_factors,
    "factor_exposure":      _render_factor_exposure,
    "regime_probability":   _render_regime_probability,
    "risk_metrics":         _render_risk_metrics,
    "lasso_coefficients":   _render_lasso_coefficients,
    "yield_curve_view":     _render_yield_curve_view,
    "policy_outlook":       _render_policy_outlook,
    "cross_asset_matrix":   _render_cross_asset_matrix,
}


def report(result: EcoResult, profile: dict | None = None) -> str:
    """EcoResult를 프로필 설정에 따라 저장하고 콘솔 출력."""
    if profile is None:
        profile = {}

    report_cfg  = profile.get("report", {})
    fmt         = report_cfg.get("format", "brief")
    sections    = report_cfg.get("sections", ["signal", "confidence", "rationale", "key_factors"])
    audience    = report_cfg.get("audience", "general")
    profile_name = profile.get("name", "base")

    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    # JSON 저장
    filename = f"eco_{result.date}_{profile_name}.json"
    path = os.path.join(output_dir, filename)
    payload = result.to_dict()
    payload.update({"_profile": profile_name, "_format": fmt, "_audience": audience})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # 콘솔 출력
    width = 58
    print(f"\n{'='*width}")
    print(f"  eco_system  |  {profile_name.upper()}  |  대상: {audience}")
    print(f"{'─'*width}")

    for section in sections:
        renderer = SECTION_RENDERERS.get(section)
        if renderer:
            line = renderer(result, profile)
            if line:
                print(line)

    # detailed / dashboard: 에이전트별 응답 추가 출력
    if fmt in ("detailed", "dashboard") and result.agent_responses:
        print(f"{'─'*width}")
        print("  [에이전트별 응답]")
        for resp in result.agent_responses:
            e = SIGNAL_EMOJI.get(resp.signal.value, "❓")
            print(f"    [{resp.agent:10s}] {e} {resp.signal.value:8s} ({resp.confidence:.0%})")
            print(f"               {resp.rationale[:70]}")

    print(f"{'─'*width}")
    print(f"  저장: {path}")
    print(f"{'='*width}\n")

    return path
