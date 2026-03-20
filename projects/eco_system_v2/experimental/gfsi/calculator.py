"""
experimental/gfsi/calculator.py — GFSI 점수 산출 (v0.3)

5채널: crypto_vol, stable_flow, geo_stress, news_stress, liquidity
각 채널의 raw 데이터를 0-100 점수로 변환한 뒤 가중 합산.
0 = 극단 공포/스트레스, 100 = 극단 탐욕/안정.
"""

from __future__ import annotations

import logging
from typing import Any

from .domain import (
    BTC_VOL_RATIO_HIGH,
    BTC_VOL_RATIO_LOW,
    CHANNEL_WEIGHTS,
    Channel,
    ChannelScore,
    EPU_HIGH,
    EPU_LOW,
    GFSIResult,
    GPR_HIGH,
    GPR_LOW,
    OIL_GOLD_CORR_HIGH,
    RRP_ABS_CHANGE_B,
    RRP_NEAR_ZERO_B,
    STABLE_MCAP_CHANGE_HIGH,
    STABLE_MCAP_CHANGE_LOW,
    TGA_CENTER_B,
    TGA_DEVIATION_HIGH_B,
    TGA_DEVIATION_LOW_B,
    classify_level,
    get_weight,
)

logger = logging.getLogger(__name__)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _linear_scale(
    value: float,
    low: float,
    high: float,
    invert: bool = False,
) -> float:
    """value를 [low, high] → [0, 100]으로 선형 스케일."""
    if high == low:
        return 50.0
    score = (value - low) / (high - low) * 100
    if invert:
        score = 100.0 - score
    return _clamp(score)


# ============================================================================
# 채널별 점수 산출
# ============================================================================

def score_crypto_vol(data: dict[str, Any]) -> ChannelScore:
    """BTC 변동성 + ETH/BTC 비율 → 0-100."""
    quality = 1.0
    sub_scores: list[tuple] = []

    vol_ratio = data.get("btc_vol_ratio")
    if vol_ratio is not None:
        s = _linear_scale(vol_ratio, BTC_VOL_RATIO_LOW * 0.7, BTC_VOL_RATIO_HIGH * 1.3, invert=True)
        sub_scores.append(("vol_ratio", s, 0.6))
    else:
        quality -= 0.3

    btc_ret = data.get("btc_return_7d")
    if btc_ret is not None:
        s = _linear_scale(btc_ret, -15.0, 15.0)
        sub_scores.append(("btc_7d", s, 0.25))
    else:
        quality -= 0.1

    eth_btc = data.get("eth_btc_ratio")
    eth_btc_avg = data.get("eth_btc_ratio_20d_avg")
    if eth_btc is not None and eth_btc_avg is not None and eth_btc_avg > 0:
        pct_diff = (eth_btc / eth_btc_avg - 1) * 100
        s = _linear_scale(pct_diff, -10.0, 10.0)
        sub_scores.append(("eth_btc", s, 0.15))

    if not sub_scores:
        return ChannelScore(
            channel=Channel.CRYPTO_VOL, score=50.0,
            raw_values=data, signal="data unavailable", data_quality=0.0,
        )

    total_w = sum(w for _, _, w in sub_scores)
    score = sum(s * w for _, s, w in sub_scores) / total_w

    signal = "stable" if score >= 60 else "stress" if score <= 40 else "neutral"
    return ChannelScore(
        channel=Channel.CRYPTO_VOL, score=round(score, 2),
        raw_values=data, signal=signal, data_quality=round(quality, 2),
    )


def score_stable_flow(data: dict[str, Any]) -> ChannelScore:
    """스테이블코인 유입/유출 + DeFi TVL → 0-100."""
    quality = 1.0
    sub_scores: list[tuple] = []

    mcap_chg = data.get("stablecoin_mcap_change_7d_pct")
    if mcap_chg is not None:
        s = _linear_scale(mcap_chg, STABLE_MCAP_CHANGE_LOW, STABLE_MCAP_CHANGE_HIGH)
        sub_scores.append(("stable_mcap", s, 0.6))
    else:
        quality -= 0.3

    tvl_chg = data.get("defi_tvl_change_7d_pct")
    if tvl_chg is not None:
        s = _linear_scale(tvl_chg, -5.0, 5.0)
        sub_scores.append(("defi_tvl", s, 0.4))
    else:
        quality -= 0.2

    if not sub_scores:
        return ChannelScore(
            channel=Channel.STABLE_FLOW, score=50.0,
            raw_values=data, signal="data unavailable", data_quality=0.0,
        )

    total_w = sum(w for _, _, w in sub_scores)
    score = sum(s * w for _, s, w in sub_scores) / total_w

    signal = "inflow" if score >= 60 else "outflow" if score <= 40 else "flat"
    return ChannelScore(
        channel=Channel.STABLE_FLOW, score=round(score, 2),
        raw_values=data, signal=signal, data_quality=round(quality, 2),
    )


def score_geo_stress(data: dict[str, Any]) -> ChannelScore:
    """GPR 텍스트 + 유가·금 가격 → 0-100.

    v0.3: GPR Index가 primary (40%), 유가·금은 confirmation.
    GPR이 없으면 가격 프록시만으로 폴백.
    """
    quality = 1.0
    sub_scores: list[tuple] = []
    has_gpr = False

    # GPR Index — primary 텍스트 시그널 (비중 40%)
    gpr = data.get("gpr_current")
    if gpr is not None:
        has_gpr = True
        # GPR 높을수록 지정학 위험 → 점수 낮음
        s = _linear_scale(gpr, GPR_LOW, GPR_HIGH, invert=True)
        sub_scores.append(("gpr", s, 0.40))
    else:
        quality -= 0.2

    # 유가-금 20일 상관 — confirmation (비중 25% or GPR 없으면 50%)
    corr_weight = 0.25 if has_gpr else 0.50
    corr = data.get("oil_gold_corr_20d")
    if corr is not None:
        s = _linear_scale(corr, -0.5, OIL_GOLD_CORR_HIGH + 0.2, invert=True)
        sub_scores.append(("og_corr", s, corr_weight))
    else:
        quality -= 0.15

    # 유가 7일 변화 (비중 20% or GPR 없으면 30%)
    oil_weight = 0.20 if has_gpr else 0.30
    oil_chg = data.get("oil_change_7d_pct")
    if oil_chg is not None:
        s = _linear_scale(oil_chg, -10.0, 10.0, invert=True)
        sub_scores.append(("oil_7d", s, oil_weight))

    # 금 vs MA20 (비중 15% or GPR 없으면 20%)
    gold_weight = 0.15 if has_gpr else 0.20
    gold_ma = data.get("gold_vs_ma20_pct")
    if gold_ma is not None:
        s = _linear_scale(gold_ma, -5.0, 5.0, invert=True)
        sub_scores.append(("gold_ma", s, gold_weight))

    if not sub_scores:
        return ChannelScore(
            channel=Channel.GEO_STRESS, score=50.0,
            raw_values=data, signal="data unavailable", data_quality=0.0,
        )

    total_w = sum(w for _, _, w in sub_scores)
    score = sum(s * w for _, s, w in sub_scores) / total_w

    signal = "calm" if score >= 60 else "tension" if score <= 40 else "monitoring"
    return ChannelScore(
        channel=Channel.GEO_STRESS, score=round(score, 2),
        raw_values=data, signal=signal, data_quality=round(quality, 2),
    )


def score_news_stress(data: dict[str, Any]) -> ChannelScore:
    """EPU (Economic Policy Uncertainty) → 0-100.

    EPU 높을수록 정책 불확실성 → 점수 낮음.
    7일 변화로 추세 반영.
    """
    if data.get("note"):
        return ChannelScore(
            channel=Channel.NEWS_STRESS, score=50.0,
            raw_values=data, signal="no API key", data_quality=0.0,
        )

    epu = data.get("epu_current")
    if epu is None:
        return ChannelScore(
            channel=Channel.NEWS_STRESS, score=50.0,
            raw_values=data, signal="data unavailable", data_quality=0.0,
        )

    quality = 1.0
    sub_scores: list[tuple] = []

    # EPU 현재 수준 — 비중 70%
    s = _linear_scale(epu, EPU_LOW, EPU_HIGH, invert=True)
    sub_scores.append(("epu_level", s, 0.70))

    # EPU 7일 변화 — 비중 30% (급등하면 추가 스트레스)
    epu_chg = data.get("epu_change_7d")
    if epu_chg is not None:
        # 변화량을 점수화: -100 → 100점(개선), +100 → 0점(악화)
        s = _linear_scale(epu_chg, -100.0, 100.0, invert=True)
        sub_scores.append(("epu_trend", s, 0.30))
    else:
        quality -= 0.1

    total_w = sum(w for _, _, w in sub_scores)
    score = sum(s * w for _, s, w in sub_scores) / total_w

    signal = "certain" if score >= 60 else "uncertain" if score <= 40 else "mixed"
    return ChannelScore(
        channel=Channel.NEWS_STRESS, score=round(score, 2),
        raw_values=data, signal=signal, data_quality=round(quality, 2),
    )


def _score_rrp(data: dict[str, Any]) -> float | None:
    """RRP 서브지표 점수. near-zero 대응 포함."""
    rrp_current = data.get("rrp_current_b")
    if rrp_current is None:
        return None

    if rrp_current < RRP_NEAR_ZERO_B:
        return 75.0

    rrp_chg_abs = data.get("rrp_change_7d_abs_b")
    if rrp_chg_abs is not None:
        return _linear_scale(rrp_chg_abs, -RRP_ABS_CHANGE_B, RRP_ABS_CHANGE_B, invert=True)

    rrp_chg_pct = data.get("rrp_change_7d_pct")
    if rrp_chg_pct is not None:
        return _linear_scale(rrp_chg_pct, -10.0, 10.0, invert=True)

    return None


def _score_tga(data: dict[str, Any]) -> float | None:
    """TGA 서브지표 점수. 비대칭 처리."""
    tga = data.get("tga_current_b")
    if tga is None:
        return None

    deviation = tga - TGA_CENTER_B

    if deviation < -TGA_DEVIATION_LOW_B:
        effective_tga = max(tga, 0.0)
        return _linear_scale(
            effective_tga, 0.0, TGA_CENTER_B - TGA_DEVIATION_LOW_B,
        ) * 0.3
    elif deviation > TGA_DEVIATION_HIGH_B:
        excess = deviation - TGA_DEVIATION_HIGH_B
        return _clamp(70.0 - _linear_scale(excess, 0.0, 400.0) * 0.4, 30.0, 70.0)
    else:
        abs_dev = abs(deviation)
        max_dev = max(TGA_DEVIATION_LOW_B, TGA_DEVIATION_HIGH_B)
        return _clamp(70.0 + _linear_scale(abs_dev, 0.0, max_dev, invert=True) * 0.3,
                      70.0, 100.0)


def score_liquidity(data: dict[str, Any]) -> ChannelScore:
    """Fed RRP + TGA → 0-100."""
    if data.get("note"):
        return ChannelScore(
            channel=Channel.LIQUIDITY, score=50.0,
            raw_values=data, signal="no API key", data_quality=0.0,
        )

    quality = 1.0
    sub_scores: list[tuple] = []

    rrp_score = _score_rrp(data)
    if rrp_score is not None:
        sub_scores.append(("rrp", rrp_score, 0.6))
    else:
        quality -= 0.3

    tga_score = _score_tga(data)
    if tga_score is not None:
        sub_scores.append(("tga", tga_score, 0.4))

    if not sub_scores:
        return ChannelScore(
            channel=Channel.LIQUIDITY, score=50.0,
            raw_values=data, signal="partial data", data_quality=0.0,
        )

    total_w = sum(w for _, _, w in sub_scores)
    score = sum(s * w for _, s, w in sub_scores) / total_w

    signal = "ample" if score >= 60 else "tight" if score <= 40 else "neutral"
    return ChannelScore(
        channel=Channel.LIQUIDITY, score=round(score, 2),
        raw_values=data, signal=signal, data_quality=round(quality, 2),
    )


# ============================================================================
# GFSI 종합 산출
# ============================================================================

CHANNEL_SCORERS = {
    Channel.CRYPTO_VOL: score_crypto_vol,
    Channel.STABLE_FLOW: score_stable_flow,
    Channel.GEO_STRESS: score_geo_stress,
    Channel.NEWS_STRESS: score_news_stress,
    Channel.LIQUIDITY: score_liquidity,
}


def calculate_gfsi(raw_data: dict[str, dict]) -> GFSIResult:
    """전체 raw 데이터 → GFSI 종합 점수."""
    channel_scores: list[ChannelScore] = []

    for ch in Channel:
        scorer = CHANNEL_SCORERS[ch]
        ch_data = raw_data.get(ch.value, {})
        cs = scorer(ch_data)
        channel_scores.append(cs)

    weighted_sum = 0.0
    total_weight = 0.0

    for cs in channel_scores:
        w = get_weight(cs.channel) * cs.data_quality
        weighted_sum += cs.score * w
        total_weight += w

    gfsi_score = weighted_sum / total_weight if total_weight > 0 else 50.0
    gfsi_score = _clamp(gfsi_score)

    vix = raw_data.get("vix", {}).get("vix_current", 0.0)

    return GFSIResult(
        score=round(gfsi_score, 2),
        level=classify_level(gfsi_score),
        channels=tuple(channel_scores),
        vix_current=vix,
    )
