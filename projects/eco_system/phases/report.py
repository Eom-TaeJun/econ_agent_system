"""
eco_system Phase 3: 결과 저장 및 출력
프로필의 report 설정(format, sections, audience)에 따라 출력 형식 결정
"""

import json
import os
from core.schemas import EcoResult

SIGNAL_EMOJI = {"BULLISH": "📈", "NEUTRAL": "➡️", "BEARISH": "📉"}

# 섹션 렌더러 — 필요한 섹션만 출력
SECTION_RENDERERS = {
    "signal":         lambda r, _: f"  신호: {SIGNAL_EMOJI.get(r.consensus_signal.value,'❓')} {r.consensus_signal.value}",
    "confidence":     lambda r, _: f"  신뢰도: {r.consensus_confidence:.0%}",
    "rationale":      lambda r, _: f"  근거: {r.summary}",
    "key_factors":    lambda r, _: (
        "  핵심 요인:\n" + "\n".join(f"    • {f}" for f in r.key_factors)
        if r.key_factors else ""
    ),
    "sector_breakdown": lambda r, _: "  [섹터 분석]: 추후 구현",
    "top_picks":        lambda r, _: "  [Top Picks]: 추후 구현",
    "risk_factors":     lambda r, _: "  [리스크 요인]: 추후 구현",
    "lasso_coefficients": lambda r, _: "  [LASSO 계수]: 추후 구현",
    "regime_probability": lambda r, _: "  [레짐 확률]: 추후 구현",
    "factor_exposure":  lambda r, _: "  [팩터 노출도]: 추후 구현",
    "risk_metrics":     lambda r, _: "  [리스크 지표]: 추후 구현",
    "policy_outlook":   lambda r, _: "  [통화정책 전망]: 추후 구현",
    "yield_curve_view": lambda r, _: "  [금리 커브 뷰]: 추후 구현",
    "cross_asset_matrix": lambda r, _: "  [크로스에셋 매트릭스]: 추후 구현",
}


def report(result: EcoResult, profile: dict | None = None) -> str:
    """
    EcoResult를 프로필 설정에 따라 저장하고 콘솔 출력.
    - format: brief | detailed | dashboard
    - sections: 출력할 섹션 목록
    - audience: 대상 독자 (콘솔 헤더에 표시)
    """
    if profile is None:
        profile = {}

    report_cfg = profile.get("report", {})
    fmt = report_cfg.get("format", "brief")
    sections = report_cfg.get("sections", ["signal", "confidence", "rationale", "key_factors"])
    audience = report_cfg.get("audience", "general")
    profile_name = profile.get("name", "base")

    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    # JSON 저장 (항상)
    filename = f"eco_{result.date}_{profile_name}.json"
    path = os.path.join(output_dir, filename)
    payload = result.to_dict()
    payload["_profile"] = profile_name
    payload["_format"] = fmt
    payload["_audience"] = audience

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # 콘솔 출력
    width = 54
    print(f"\n{'='*width}")
    print(f"  eco_system | 프로필: {profile_name.upper()} | 대상: {audience}")
    print(f"{'─'*width}")

    for section in sections:
        renderer = SECTION_RENDERERS.get(section)
        if renderer:
            line = renderer(result, profile)
            if line:
                print(line)

    # detailed / dashboard는 에이전트별 응답 추가 출력
    if fmt in ("detailed", "dashboard") and result.agent_responses:
        print(f"{'─'*width}")
        print("  에이전트별 응답:")
        for resp in result.agent_responses:
            emoji = SIGNAL_EMOJI.get(resp.signal.value, "❓")
            print(f"    [{resp.agent}] {emoji} {resp.signal.value} ({resp.confidence:.0%})")
            print(f"    → {resp.rationale[:80]}")

    print(f"{'─'*width}")
    print(f"  저장: {path}")
    print(f"{'='*width}\n")

    return path
