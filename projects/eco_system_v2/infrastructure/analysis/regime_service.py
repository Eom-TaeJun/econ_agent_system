"""
infrastructure/analysis/regime_service.py

GMM 3-State + MA 크로스오버 + 기술적 지표 기반 시장 레짐 탐지.
eimas lib/regime_detector.py에서 핵심 알고리즘 추출 + 강화.

방법론:
  1. GMM(Gaussian Mixture Model) 3-state: Returns + VIX → Bull/Neutral/Bear 확률
  2. MA 크로스오버: 50일/200일 이동평균으로 추세 판단
  3. 기술적 지표: RSI, 모멘텀, 52주 고점 대비, ADX(간소)
  4. 전환 확률: RSI + VIX 백분위 기반 추정

참고: Hamilton(1989) Markov Switching Model의 간소화 버전

인터페이스: detect_regime(price_series, vix_series) -> RegimeResult
"""

from __future__ import annotations

import logging
import math
from datetime import datetime

from domain.regime import (
    MarketRegime,
    RegimeResult,
    TrendState,
    VolatilityState,
)

logger = logging.getLogger(__name__)

# VIX 임계값
_VIX_VERY_LOW = 12.0
_VIX_LOW = 16.0
_VIX_NORMAL = 22.0
_VIX_HIGH = 30.0

# 레짐별 특성
_REGIME_INFO: dict[MarketRegime, dict[str, str]] = {
    MarketRegime.BULL_LOW_VOL: {
        "description": "최적의 투자 환경. 리스크 자산 선호",
        "strategy": "주식 비중 확대, 성장주/소형주 선호",
        "risk_appetite": "HIGH",
    },
    MarketRegime.BULL_HIGH_VOL: {
        "description": "상승세지만 조정 가능성. 차익실현 고려",
        "strategy": "분할 매도 준비, 헤지 비중 확대",
        "risk_appetite": "MEDIUM",
    },
    MarketRegime.BEAR_LOW_VOL: {
        "description": "하락세 바닥 탐색. 저점 매수 기회 탐색",
        "strategy": "분할 매수, 방어주/배당주 선호",
        "risk_appetite": "LOW_SELECTIVE",
    },
    MarketRegime.BEAR_HIGH_VOL: {
        "description": "위기 국면. 자산 보존 최우선",
        "strategy": "현금 비중 극대화, 안전자산 선호",
        "risk_appetite": "VERY_LOW",
    },
    MarketRegime.TRANSITION: {
        "description": "레짐 전환 중. 관망 필요",
        "strategy": "포지션 축소, 방향성 확인 후 진입",
        "risk_appetite": "NEUTRAL",
    },
}


def detect_regime(
    price_series: list[float],
    vix_series: list[float],
) -> RegimeResult:
    """
    가격 시리즈와 VIX 시리즈로 시장 레짐을 탐지한다.

    price_series: 최소 50개 일봉 종가
    vix_series: VIX 종가 시리즈 (price_series와 같은 기간)

    Returns: RegimeResult (domain VO)
    """
    if len(price_series) < 50:
        return _fallback_result("데이터 부족 (50개 미만)")

    # 1. 기술적 지표 계산
    indicators = _calculate_indicators(price_series, vix_series)

    # 2. 추세 판단 (지표 기반 점수)
    trend = _classify_trend(indicators)

    # 3. 변동성 판단
    vol_state = _classify_volatility(indicators["vix"])

    # 4. GMM 확률 계산
    gmm_probs = _run_gmm(price_series, vix_series)

    # 5. 레짐 결정 + 신뢰도
    regime, confidence = _determine_regime(trend, vol_state, indicators, gmm_probs)

    # 6. 전환 확률
    transition = _calculate_transition_probs(regime, indicators)

    info = _REGIME_INFO[regime]

    # GMM 로깅
    gmm_str = ", ".join(f"{k}={v:.0%}" for k, v in gmm_probs.items())
    logger.info(
        f"[regime] {regime.value} (conf={confidence:.0%}), "
        f"trend={trend.value}, vol={vol_state.value}, "
        f"GMM=[{gmm_str}], RSI={indicators['rsi']:.0f}"
    )

    return RegimeResult(
        regime=regime,
        confidence=confidence,
        trend_state=trend,
        volatility_state=vol_state,
        description=info["description"],
        strategy=info["strategy"],
        risk_appetite=info["risk_appetite"],
        gmm_probabilities=tuple(gmm_probs.items()),
        indicators=tuple(
            (k, round(v, 2)) for k, v in indicators.items()
        ),
        transition_probs=tuple(transition.items()),
    )


# ============================================================================
# 기술적 지표
# ============================================================================

def _calculate_indicators(
    prices: list[float],
    vix_series: list[float],
) -> dict[str, float]:
    """기술적 지표 계산."""
    current = prices[-1]
    ma50 = _sma(prices, 50)
    ma200 = _sma(prices, 200) if len(prices) >= 200 else _sma(prices, len(prices))

    # RSI 14
    rsi = _rsi(prices, 14)

    # 20일 모멘텀 (%)
    momentum_20d = ((current / prices[-20]) - 1) * 100 if len(prices) >= 20 else 0.0

    # 52주(252일) 고점 대비 (%)
    high_252 = max(prices[-252:]) if len(prices) >= 252 else max(prices)
    distance_from_high = ((current / high_252) - 1) * 100

    # VIX
    vix = vix_series[-1] if vix_series else 20.0

    # VIX 백분위 (전체 기간 중 현재 VIX가 어느 수준인지)
    if len(vix_series) > 20:
        vix_percentile = sum(1 for v in vix_series if v < vix) / len(vix_series) * 100
    else:
        vix_percentile = 50.0

    # 실현 변동성 (20일, 연환산 %)
    realized_vol = _realized_vol(prices, 20)

    return {
        "price": current,
        "ma50": ma50,
        "ma200": ma200,
        "price_above_ma50": float(current > ma50),
        "price_above_ma200": float(current > ma200),
        "ma50_above_ma200": float(ma50 > ma200),
        "rsi": rsi,
        "momentum_20d": momentum_20d,
        "distance_from_high": distance_from_high,
        "vix": vix,
        "vix_percentile": vix_percentile,
        "realized_vol_20d": realized_vol,
    }


def _rsi(prices: list[float], period: int = 14) -> float:
    """RSI (Relative Strength Index)."""
    if len(prices) < period + 1:
        return 50.0

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    recent = deltas[-(period * 3):]  # 충분한 lookback

    gains = [d if d > 0 else 0.0 for d in recent]
    losses = [-d if d < 0 else 0.0 for d in recent]

    # Wilder 평활 (EMA 방식)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _realized_vol(prices: list[float], window: int = 20) -> float:
    """실현 변동성 (연환산 %)."""
    if len(prices) < window + 1:
        return 0.0
    returns = [(prices[i] / prices[i - 1]) - 1.0 for i in range(-window, 0)]
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(variance) * math.sqrt(252) * 100


# ============================================================================
# 추세 판단 (eimas 스타일 점수 기반)
# ============================================================================

def _classify_trend(ind: dict[str, float]) -> TrendState:
    """MA + RSI + 모멘텀 + 고점 대비 → 점수 기반 추세 판단."""
    score = 0

    # 가격 위치
    if ind["price_above_ma50"]:
        score += 1
    if ind["price_above_ma200"]:
        score += 1
    if ind["ma50_above_ma200"]:
        score += 1

    # 고점 대비 거리
    if ind["distance_from_high"] > -5:
        score += 1
    elif ind["distance_from_high"] < -15:
        score -= 2

    # 모멘텀
    if ind["momentum_20d"] > 5:
        score += 1
    elif ind["momentum_20d"] < -5:
        score -= 1

    # RSI 극단값
    if ind["rsi"] > 70:
        score += 0  # 과매수 — 추세 강도 인정하되 반전 가능
    elif ind["rsi"] < 30:
        score -= 0  # 과매도 — 마찬가지

    # 판정
    if score >= 4:
        return TrendState.STRONG_UP
    elif score >= 2:
        return TrendState.WEAK_UP
    elif score <= -2:
        return TrendState.STRONG_DOWN
    elif score < 0:
        return TrendState.WEAK_DOWN
    else:
        return TrendState.NEUTRAL


# ============================================================================
# GMM 3-State
# ============================================================================

def _run_gmm(
    price_series: list[float],
    vix_series: list[float],
) -> dict[str, float]:
    """
    GMM 기반 Bull/Neutral/Bear 확률.

    Returns + VIX 2차원 데이터로 3-component GMM 학습.
    VIX 평균이 낮은 컴포넌트 = Bull, 높은 = Bear.
    sklearn 없으면 규칙 기반 fallback.
    """
    try:
        import numpy as np
        from sklearn.mixture import GaussianMixture
    except ImportError:
        logger.warning("[regime] sklearn 미설치 — GMM 스킵, 규칙 기반 fallback")
        return _gmm_fallback(price_series, vix_series)

    # 최소 길이 맞추기
    min_len = min(len(price_series), len(vix_series))
    if min_len < 60:
        return _gmm_fallback(price_series, vix_series)

    prices = price_series[-min_len:]
    vix = vix_series[-min_len:]

    # 일간 수익률
    returns = [(prices[i] / prices[i - 1]) - 1.0 for i in range(1, len(prices))]
    vix_aligned = vix[1:]  # 수익률과 길이 맞춤

    if len(returns) < 50:
        return _gmm_fallback(price_series, vix_series)

    X = np.column_stack([returns, vix_aligned])

    gmm = GaussianMixture(
        n_components=3,
        covariance_type="full",
        random_state=42,
        n_init=3,
    )
    gmm.fit(X)

    # VIX 평균 기준 정렬: Low VIX → Bull, High VIX → Bear
    vix_means = gmm.means_[:, 1]
    sorted_idx = np.argsort(vix_means)

    label_map = {
        int(sorted_idx[0]): "Bull",
        int(sorted_idx[1]): "Neutral",
        int(sorted_idx[2]): "Bear",
    }

    # 현재 상태 확률
    current_x = X[-1].reshape(1, -1)
    probs = gmm.predict_proba(current_x)[0]

    result = {}
    for i, prob in enumerate(probs):
        result[label_map[i]] = round(float(prob), 4)

    return result


def _gmm_fallback(
    price_series: list[float],
    vix_series: list[float],
) -> dict[str, float]:
    """sklearn 없을 때 규칙 기반 GMM 대체."""
    vix = vix_series[-1] if vix_series else 20.0
    ret_20d = (price_series[-1] / price_series[-20] - 1) if len(price_series) >= 20 else 0.0

    if ret_20d > 0.02 and vix < 20:
        return {"Bull": 0.70, "Neutral": 0.20, "Bear": 0.10}
    elif ret_20d < -0.02 and vix > 25:
        return {"Bull": 0.10, "Neutral": 0.20, "Bear": 0.70}
    elif vix > 30:
        return {"Bull": 0.05, "Neutral": 0.15, "Bear": 0.80}
    else:
        return {"Bull": 0.33, "Neutral": 0.34, "Bear": 0.33}


# ============================================================================
# 변동성
# ============================================================================

def _classify_volatility(vix: float) -> VolatilityState:
    """VIX 절대 수준으로 변동성 상태 분류."""
    if vix < _VIX_VERY_LOW:
        return VolatilityState.VERY_LOW
    elif vix < _VIX_LOW:
        return VolatilityState.LOW
    elif vix < _VIX_NORMAL:
        return VolatilityState.NORMAL
    elif vix < _VIX_HIGH:
        return VolatilityState.HIGH
    else:
        return VolatilityState.EXTREME


# ============================================================================
# 레짐 결정 + 신뢰도
# ============================================================================

def _determine_regime(
    trend: TrendState,
    vol: VolatilityState,
    indicators: dict[str, float],
    gmm_probs: dict[str, float],
) -> tuple[MarketRegime, float]:
    """추세 + 변동성 + GMM으로 레짐 결정 + 신뢰도."""
    is_bullish = trend in (TrendState.STRONG_UP, TrendState.WEAK_UP)
    is_bearish = trend in (TrendState.STRONG_DOWN, TrendState.WEAK_DOWN)
    is_low_vol = vol in (VolatilityState.VERY_LOW, VolatilityState.LOW)
    is_high_vol = vol in (VolatilityState.HIGH, VolatilityState.EXTREME)

    # 규칙 기반 레짐
    if is_bullish and is_low_vol:
        regime = MarketRegime.BULL_LOW_VOL
        base_conf = 0.90 if trend == TrendState.STRONG_UP else 0.75
    elif is_bullish and is_high_vol:
        regime = MarketRegime.BULL_HIGH_VOL
        base_conf = 0.80 if trend == TrendState.STRONG_UP else 0.65
    elif is_bearish and is_low_vol:
        regime = MarketRegime.BEAR_LOW_VOL
        base_conf = 0.85 if trend == TrendState.STRONG_DOWN else 0.70
    elif is_bearish and is_high_vol:
        regime = MarketRegime.BEAR_HIGH_VOL
        base_conf = 0.90 if vol == VolatilityState.EXTREME else 0.75
    else:
        regime = MarketRegime.TRANSITION
        base_conf = 0.50

    # GMM 확률로 신뢰도 조정
    gmm_bull = gmm_probs.get("Bull", 0.33)
    gmm_bear = gmm_probs.get("Bear", 0.33)

    if is_bullish and gmm_bull > 0.5:
        base_conf = min(1.0, base_conf + 0.05)  # GMM이 Bull 동의
    elif is_bullish and gmm_bear > 0.5:
        base_conf = max(0.3, base_conf - 0.15)  # GMM이 반대
    elif is_bearish and gmm_bear > 0.5:
        base_conf = min(1.0, base_conf + 0.05)
    elif is_bearish and gmm_bull > 0.5:
        base_conf = max(0.3, base_conf - 0.15)

    # 모멘텀 일관성 보너스
    momentum = indicators.get("momentum_20d", 0)
    if (is_bullish and momentum > 0) or (is_bearish and momentum < 0):
        base_conf = min(1.0, base_conf + 0.03)

    return regime, round(base_conf, 4)


# ============================================================================
# 전환 확률
# ============================================================================

def _calculate_transition_probs(
    regime: MarketRegime,
    indicators: dict[str, float],
) -> dict[str, float]:
    """RSI + VIX 백분위 기반 전환 확률 추정."""
    stay_prob = 70.0
    rsi = indicators.get("rsi", 50)
    vix_pct = indicators.get("vix_percentile", 50)

    # RSI 극단값 → 레짐 유지 확률 감소
    if rsi > 70 and regime in (MarketRegime.BULL_LOW_VOL, MarketRegime.BULL_HIGH_VOL):
        stay_prob -= 15  # 과매수 상태에서 Bull 유지 어려움
    elif rsi < 30 and regime in (MarketRegime.BEAR_LOW_VOL, MarketRegime.BEAR_HIGH_VOL):
        stay_prob -= 15  # 과매도 상태에서 Bear 유지 어려움

    # VIX 백분위 극단 → 변동성 전환 가능
    if vix_pct > 80:
        stay_prob -= 10
    elif vix_pct < 20:
        stay_prob += 5

    # 고점 대비 거리
    dist = indicators.get("distance_from_high", 0)
    if dist < -20:
        stay_prob -= 5  # 큰 낙폭 → 전환 가능성 up

    stay_prob = max(30.0, min(95.0, stay_prob))

    return {
        "stay": round(stay_prob, 1),
        "transition": round(100.0 - stay_prob, 1),
    }


# ============================================================================
# 유틸리티
# ============================================================================

def _sma(series: list[float], window: int) -> float:
    """단순이동평균."""
    if len(series) < window:
        return sum(series) / len(series) if series else 0.0
    return sum(series[-window:]) / window


def _fallback_result(reason: str) -> RegimeResult:
    """데이터 부족 시 기본값."""
    return RegimeResult(
        regime=MarketRegime.TRANSITION,
        confidence=0.0,
        trend_state=TrendState.NEUTRAL,
        volatility_state=VolatilityState.NORMAL,
        description=f"판단 불가: {reason}",
        strategy="데이터 확보 후 재분석",
        risk_appetite="NEUTRAL",
    )
