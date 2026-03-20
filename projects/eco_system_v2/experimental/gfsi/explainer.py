"""
experimental/gfsi/explainer.py — GFSI 산출 과정 전체 추적 (v0.3)

5채널: crypto_vol, stable_flow, geo_stress, news_stress, liquidity
"""

from __future__ import annotations

from .domain import (
    BTC_VOL_RATIO_HIGH,
    BTC_VOL_RATIO_LOW,
    CHANNEL_WEIGHTS,
    Channel,
    EPU_HIGH,
    EPU_LOW,
    GFSIResult,
    GPR_HIGH,
    GPR_LOW,
    OIL_GOLD_CORR_HIGH,
    RRP_NEAR_ZERO_B,
    STABLE_MCAP_CHANGE_HIGH,
    STABLE_MCAP_CHANGE_LOW,
    TGA_CENTER_B,
    TGA_DEVIATION_HIGH_B,
    TGA_DEVIATION_LOW_B,
    get_weight,
)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _ls(value: float, low: float, high: float, invert: bool = False) -> float:
    if high == low:
        return 50.0
    score = (value - low) / (high - low) * 100
    if invert:
        score = 100.0 - score
    return _clamp(score)


def _scale_formula(
    name: str,
    value: float,
    low: float,
    high: float,
    invert: bool,
    weight: float,
) -> list[str]:
    """서브지표 하나의 산출 과정을 텍스트로 반환."""
    lines: list[str] = []
    raw_score = (value - low) / (high - low) * 100
    final = 100.0 - raw_score if invert else raw_score
    clamped = _clamp(final)
    was_clamped = clamped != final

    lines.append(f"  {name}:")
    lines.append(f"    값: {value:.4f}")
    lines.append(f"    범위: [{low}, {high}] {'(반전)' if invert else ''}")

    if invert:
        lines.append(f"    계산: 100 - ({value:.4f} - {low}) / ({high} - {low}) × 100")
        lines.append(f"         = 100 - {raw_score:.2f} = {final:.2f}")
    else:
        lines.append(f"    계산: ({value:.4f} - {low}) / ({high} - {low}) × 100 = {raw_score:.2f}")

    if was_clamped:
        lines.append(f"    클램프: {final:.2f} → {clamped:.2f}")

    lines.append(f"    점수: {clamped:.1f} (비중 {weight:.0%})")
    return lines


# ============================================================================
# 채널별 설명
# ============================================================================

def _explain_crypto_vol(data: dict) -> tuple[list[str], list[tuple]]:
    lines: list[str] = []
    subs: list[tuple] = []

    lines.append("## 1. crypto_vol (BTC 변동성) — 가중 25%")
    lines.append("")
    lines.append("24/7 핵심 채널. BTC 시장의 단기 변동성 구조.")
    lines.append("")

    vol_low = BTC_VOL_RATIO_LOW * 0.7
    vol_high = BTC_VOL_RATIO_HIGH * 1.3

    vr = data.get("btc_vol_ratio")
    if vr is not None:
        s = _ls(vr, vol_low, vol_high, invert=True)
        lines.extend(_scale_formula(
            "btc_vol_ratio (20d/60d)", vr, vol_low, vol_high, True, 0.6,
        ))
        lines.append("")
        subs.append(("vol_ratio", s, 0.6))

    ret = data.get("btc_return_7d")
    if ret is not None:
        s = _ls(ret, -15.0, 15.0)
        lines.extend(_scale_formula("btc_return_7d", ret, -15.0, 15.0, False, 0.25))
        lines.append("")
        subs.append(("btc_7d", s, 0.25))

    eth_btc = data.get("eth_btc_ratio")
    eth_btc_avg = data.get("eth_btc_ratio_20d_avg")
    if eth_btc is not None and eth_btc_avg is not None and eth_btc_avg > 0:
        pct = (eth_btc / eth_btc_avg - 1) * 100
        s = _ls(pct, -10.0, 10.0)
        lines.extend(_scale_formula(
            f"eth_btc 변화 ({pct:+.2f}%)", pct, -10.0, 10.0, False, 0.15,
        ))
        lines.append("")
        subs.append(("eth_btc", s, 0.15))

    return lines, subs


def _explain_stable_flow(data: dict) -> tuple[list[str], list[tuple]]:
    lines: list[str] = []
    subs: list[tuple] = []

    lines.append("## 2. stable_flow (스테이블코인·DeFi) — 가중 20%")
    lines.append("")
    lines.append("24/7 온체인 채널. VIX가 전혀 못 보는 독립 정보.")
    lines.append("")

    mcap = data.get("stablecoin_mcap_change_7d_pct")
    if mcap is not None:
        s = _ls(mcap, STABLE_MCAP_CHANGE_LOW, STABLE_MCAP_CHANGE_HIGH)
        lines.extend(_scale_formula(
            "stablecoin 시총 7d변화", mcap,
            STABLE_MCAP_CHANGE_LOW, STABLE_MCAP_CHANGE_HIGH, False, 0.6,
        ))
        lines.append("")
        subs.append(("stable_mcap", s, 0.6))

    tvl = data.get("defi_tvl_change_7d_pct")
    if tvl is not None:
        s = _ls(tvl, -5.0, 5.0)
        lines.extend(_scale_formula("DeFi TVL 7d변화", tvl, -5.0, 5.0, False, 0.4))
        lines.append("")
        subs.append(("defi_tvl", s, 0.4))

    return lines, subs


def _explain_geo_stress(data: dict) -> tuple[list[str], list[tuple]]:
    lines: list[str] = []
    subs: list[tuple] = []

    lines.append("## 3. geo_stress (지정학 리스크) — 가중 25%")
    lines.append("")
    lines.append("텍스트(GPR) + 가격(유가·금) 결합. GPR이 primary, 가격은 confirmation.")
    lines.append("")

    has_gpr = False
    gpr = data.get("gpr_current")
    if gpr is not None:
        has_gpr = True
        s = _ls(gpr, GPR_LOW, GPR_HIGH, invert=True)
        lines.extend(_scale_formula(
            f"GPR Index (Caldara & Iacoviello) — 30d평균: {data.get('gpr_30d_avg', 'N/A')}",
            gpr, GPR_LOW, GPR_HIGH, True, 0.40,
        ))
        gpr_chg = data.get("gpr_change_7d")
        if gpr_chg is not None:
            lines.append(f"    7일 변화: {gpr_chg:+.1f}")
        lines.append("")
        subs.append(("gpr", s, 0.40))
    else:
        lines.append("  GPR: 데이터 없음 — 가격 프록시로 폴백 (가중치 재분배)")
        lines.append("")

    corr_w = 0.25 if has_gpr else 0.50
    corr = data.get("oil_gold_corr_20d")
    if corr is not None:
        s = _ls(corr, -0.5, OIL_GOLD_CORR_HIGH + 0.2, invert=True)
        lines.extend(_scale_formula(
            "유가-금 20d상관", corr, -0.5, OIL_GOLD_CORR_HIGH + 0.2, True, corr_w,
        ))
        lines.append("")
        subs.append(("og_corr", s, corr_w))

    oil_w = 0.20 if has_gpr else 0.30
    oil_chg = data.get("oil_change_7d_pct")
    if oil_chg is not None:
        s = _ls(oil_chg, -10.0, 10.0, invert=True)
        lines.extend(_scale_formula("유가 7d변화", oil_chg, -10.0, 10.0, True, oil_w))
        lines.append("")
        subs.append(("oil_7d", s, oil_w))

    gold_w = 0.15 if has_gpr else 0.20
    gold_ma = data.get("gold_vs_ma20_pct")
    if gold_ma is not None:
        s = _ls(gold_ma, -5.0, 5.0, invert=True)
        lines.extend(_scale_formula("금 vs MA20", gold_ma, -5.0, 5.0, True, gold_w))
        lines.append("")
        subs.append(("gold_ma", s, gold_w))

    return lines, subs


def _explain_news_stress(data: dict) -> tuple[list[str], list[tuple]]:
    lines: list[str] = []
    subs: list[tuple] = []

    lines.append("## 4. news_stress (경제정책 불확실성) — 가중 15%")
    lines.append("")
    lines.append("EPU Index (Baker, Bloom & Davis). 비군사적 리스크: 무역전쟁, 금리정책, 규제.")
    lines.append("")

    if data.get("note"):
        lines.append(f"  ⚠️ {data['note']}")
        lines.append("  data_quality=0으로 종합 산출에서 제외")
        lines.append("")
        return lines, subs

    epu = data.get("epu_current")
    if epu is not None:
        s = _ls(epu, EPU_LOW, EPU_HIGH, invert=True)
        lines.extend(_scale_formula(
            f"EPU 수준 — 30d평균: {data.get('epu_30d_avg', 'N/A')}",
            epu, EPU_LOW, EPU_HIGH, True, 0.70,
        ))
        lines.append("")
        subs.append(("epu_level", s, 0.70))

        epu_chg = data.get("epu_change_7d")
        if epu_chg is not None:
            s2 = _ls(epu_chg, -100.0, 100.0, invert=True)
            lines.extend(_scale_formula(
                "EPU 7d변화", epu_chg, -100.0, 100.0, True, 0.30,
            ))
            lines.append("")
            subs.append(("epu_trend", s2, 0.30))
    else:
        lines.append("  EPU: 데이터 없음")
        lines.append("")

    return lines, subs


def _explain_liquidity(data: dict) -> tuple[list[str], list[tuple]]:
    lines: list[str] = []
    subs: list[tuple] = []

    lines.append("## 5. liquidity (Fed 유동성) — 가중 15%")
    lines.append("")
    lines.append(f"RRP + TGA. 구조적 배경 조건. TGA 중심 ${TGA_CENTER_B:.0f}B, 비대칭.")
    lines.append("")

    if data.get("note"):
        lines.append(f"  ⚠️ {data['note']}")
        lines.append("  data_quality=0으로 종합 산출에서 제외")
        lines.append("")
        return lines, subs

    rrp_current = data.get("rrp_current_b")
    if rrp_current is not None:
        lines.append(f"  RRP: ${rrp_current:.1f}B")
        if rrp_current < RRP_NEAR_ZERO_B:
            s = 75.0
            lines.append(f"    near-zero (< ${RRP_NEAR_ZERO_B:.0f}B) → 고정 75점")
        else:
            rrp_abs = data.get("rrp_change_7d_abs_b")
            if rrp_abs is not None:
                s = _ls(rrp_abs, -50.0, 50.0, invert=True)
                lines.append(f"    7d변화: {rrp_abs:+.1f}B → 점수 {s:.1f}")
            else:
                s = 50.0
        lines.append(f"    비중 60%")
        lines.append("")
        subs.append(("rrp", s, 0.6))

    tga = data.get("tga_current_b")
    if tga is not None:
        deviation = tga - TGA_CENTER_B
        lines.append(f"  TGA: ${tga:.0f}B (중심 ${TGA_CENTER_B:.0f}B, 편차 {deviation:+.0f}B)")

        if deviation < -TGA_DEVIATION_LOW_B:
            s = _ls(max(tga, 0), 0.0, TGA_CENTER_B - TGA_DEVIATION_LOW_B) * 0.3
            lines.append(f"    위험 구간 → 최대 30점")
        elif deviation > TGA_DEVIATION_HIGH_B:
            excess = deviation - TGA_DEVIATION_HIGH_B
            s = _clamp(70.0 - _ls(excess, 0.0, 400.0) * 0.4, 30.0, 70.0)
            lines.append(f"    높음 구간 → 30-70점")
        else:
            abs_dev = abs(deviation)
            max_dev = max(TGA_DEVIATION_LOW_B, TGA_DEVIATION_HIGH_B)
            s = _clamp(70.0 + _ls(abs_dev, 0.0, max_dev, invert=True) * 0.3, 70.0, 100.0)
            lines.append(f"    적정 범위 → 70-100점")

        lines.append(f"    점수: {s:.1f} (비중 40%)")
        lines.append("")
        subs.append(("tga", s, 0.4))

    return lines, subs


# ============================================================================
# 종합 설명
# ============================================================================

CHANNEL_EXPLAINERS = [
    (Channel.CRYPTO_VOL, _explain_crypto_vol),
    (Channel.STABLE_FLOW, _explain_stable_flow),
    (Channel.GEO_STRESS, _explain_geo_stress),
    (Channel.NEWS_STRESS, _explain_news_stress),
    (Channel.LIQUIDITY, _explain_liquidity),
]


def explain_gfsi(raw_data: dict, result: GFSIResult) -> str:
    """GFSI 전체 산출 과정을 추적하는 텍스트를 반환."""
    lines: list[str] = []

    lines.append("=" * 70)
    lines.append(f"GFSI v0.3 산출 추적 (5채널)")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"일시: {result.collected_at}")
    lines.append(f"결과: GFSI {result.score:.2f} ({result.level.value}) | VIX {result.vix_current:.1f}")
    lines.append("")

    channel_contribs: list[tuple] = []

    for ch, explainer in CHANNEL_EXPLAINERS:
        ch_data = raw_data.get(ch.value, {})
        ch_lines, subs = explainer(ch_data)
        lines.extend(ch_lines)

        if subs:
            total_w = sum(w for _, _, w in subs)
            ch_score = sum(s * w for _, s, w in subs) / total_w if total_w > 0 else 50.0

            lines.append(f"  --- 합산 ---")
            for name, s, w in subs:
                lines.append(f"    {name}: {s:.1f} × {w:.0%}")
            lines.append(f"    = {ch_score:.2f}")

            weight = get_weight(ch)
            quality = 1.0
            for cs in result.channels:
                if cs.channel == ch:
                    quality = cs.data_quality
                    break
            eff_weight = weight * quality
            contrib = ch_score * eff_weight

            lines.append(f"    가중치: {weight:.0%} × 품질 {quality:.0%} = {eff_weight:.2%}")
            lines.append(f"    기여: {contrib:.2f}")
            lines.append("")

            channel_contribs.append((ch.value, ch_score, weight, quality, contrib))

    # 종합
    lines.append("=" * 70)
    lines.append("종합")
    lines.append("=" * 70)
    lines.append("")
    lines.append("| 채널 | 점수 | 가중치 | 품질 | 실효 | 기여 | 시그널 |")
    lines.append("|------|------|--------|------|------|------|--------|")

    total_ew = 0.0
    total_contrib = 0.0
    for name, score, weight, quality, contrib in channel_contribs:
        ew = weight * quality
        total_ew += ew
        total_contrib += contrib
        sig = ""
        for cs in result.channels:
            if cs.channel.value == name:
                sig = cs.signal
                break
        lines.append(f"| {name:13} | {score:5.1f} | {weight:5.0%} | {quality:4.0%} | "
                     f"{ew:5.2%} | {contrib:5.2f} | {sig} |")

    lines.append(f"| {'합계':13} | {'':5} | {'':5} | {'':4} | {total_ew:5.2%} | {total_contrib:5.2f} | |")
    lines.append("")

    gfsi = total_contrib / total_ew if total_ew > 0 else 50.0
    lines.append(f"GFSI = {total_contrib:.2f} / {total_ew:.4f} = {gfsi:.2f} ({result.level.value})")
    lines.append("")

    return "\n".join(lines)
