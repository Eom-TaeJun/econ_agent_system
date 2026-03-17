"""
infrastructure/analysis/lasso_service.py

LASSO(L1 정규화) 기반 SPX 전방 수익률 예측.
eimas lib/lasso_model.py 핵심 알고리즘 추출 + eco_system_v2 적응.

방법론:
  1. 가격/VIX 시계열에서 기술적 특성(feature) 구성
  2. 20일 전방 수익률을 타겟으로 LASSO 학습 (TimeSeriesSplit CV)
  3. 현재 시점 특성으로 전방 수익률 예측
  4. 어떤 지표가 가장 영향력 있는지 투명하게 보고

참고: Tibshirani(1996), sklearn 없으면 규칙 기반 fallback

인터페이스: forecast_with_lasso(price_series, vix_series, ...) -> LASSOForecast
"""

from __future__ import annotations

import logging
import math
from datetime import datetime

from domain.forecast import LASSOForecast
from domain.signal import Signal
from domain.thresholds import LASSO_BULLISH_RETURN, LASSO_BEARISH_RETURN

logger = logging.getLogger(__name__)

# 전방 수익률 예측 기간 (거래일)
_FORWARD_DAYS = 20


def forecast_with_lasso(
    price_series: list[float],
    vix_series: list[float],
    fed_rate: float = 0.0,
    treasury_10y: float = 0.0,
    dxy_index: float = 0.0,
) -> LASSOForecast | None:
    """
    LASSO로 20일 전방 SPX 수익률을 예측한다.

    price_series: 최소 120개 일봉 종가
    vix_series: VIX 종가 (price_series와 같은 길이)

    Returns: LASSOForecast 또는 None (데이터 부족 / sklearn 미설치)
    """
    min_len = min(len(price_series), len(vix_series))
    if min_len < 120:
        logger.warning(f"[lasso] 데이터 부족: {min_len}개 (최소 120개 필요)")
        return None

    prices = price_series[-min_len:]
    vix = vix_series[-min_len:]

    try:
        import numpy as np
        from sklearn.linear_model import LassoCV
        from sklearn.model_selection import TimeSeriesSplit
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        logger.warning("[lasso] sklearn 미설치 — LASSO 스킵")
        return _fallback_forecast(prices, vix)

    # 1. 특성 행렬 + 타겟 구성
    feature_names, X, y = _build_features_and_target(
        prices, vix, fed_rate, treasury_10y, dxy_index
    )

    if len(X) < 60:
        logger.warning(f"[lasso] 유효 관측치 부족: {len(X)}개")
        return _fallback_forecast(prices, vix)

    X_np = np.array(X)
    y_np = np.array(y)

    # 2. 표준화
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_np)

    # 3. LASSO 학습 (TimeSeriesSplit CV)
    n_splits = min(5, len(X_scaled) // 30)
    if n_splits < 2:
        n_splits = 2

    cv = TimeSeriesSplit(n_splits=n_splits)
    alphas = np.logspace(-4, 0, 30)

    try:
        lasso = LassoCV(
            alphas=alphas,
            cv=cv,
            max_iter=10000,
            tol=1e-4,
            random_state=42,
        )
        lasso.fit(X_scaled, y_np)
    except Exception as e:
        logger.warning(f"[lasso] 학습 실패: {e}")
        return _fallback_forecast(prices, vix)

    # 4. 결과 추출
    coefficients = lasso.coef_
    selected_idx = np.where(coefficients != 0)[0]

    # R² 계산
    y_pred_train = lasso.predict(X_scaled)
    ss_res = np.sum((y_np - y_pred_train) ** 2)
    ss_tot = np.sum((y_np - y_np.mean()) ** 2)
    r_squared = max(0.0, 1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    # 5. 현재 시점 예측
    current_features = X_scaled[-1].reshape(1, -1)
    predicted_return = float(lasso.predict(current_features)[0])

    # 6. 주요 동인 (절대 계수 상위)
    abs_coefs = np.abs(coefficients)
    top_k = min(5, len(selected_idx))
    if top_k > 0:
        top_idx = selected_idx[np.argsort(abs_coefs[selected_idx])[-top_k:][::-1]]
    else:
        # 선택된 변수 없으면 절대값 상위 3개
        top_idx = np.argsort(abs_coefs)[-3:][::-1]

    key_drivers = tuple(
        (feature_names[i], round(float(coefficients[i]), 4))
        for i in top_idx
    )

    # 7. 신호 결정
    if predicted_return > LASSO_BULLISH_RETURN.value:
        signal = Signal.BULLISH
    elif predicted_return < LASSO_BEARISH_RETURN.value:
        signal = Signal.BEARISH
    else:
        signal = Signal.NEUTRAL

    # 신뢰도: R² 기반 + 예측값 크기 보정
    base_conf = min(0.9, r_squared * 1.2)  # R²가 높을수록 신뢰
    magnitude_bonus = min(0.1, abs(predicted_return) / 10)  # 강한 예측 = 약간 보너스
    confidence = round(min(1.0, max(0.2, base_conf + magnitude_bonus)), 4)

    n_selected = len(selected_idx)

    # 8. 설명
    explanation = _build_explanation(
        predicted_return=predicted_return,
        signal=signal,
        r_squared=r_squared,
        key_drivers=key_drivers,
        n_observations=len(X),
        n_selected=n_selected,
        lambda_opt=float(lasso.alpha_),
    )

    logger.info(
        f"[lasso] pred_return={predicted_return:+.2f}%, "
        f"signal={signal.value}, R²={r_squared:.3f}, "
        f"selected={n_selected}/{len(feature_names)}"
    )

    return LASSOForecast(
        predicted_return=round(predicted_return, 4),
        signal=signal,
        confidence=confidence,
        key_drivers=key_drivers,
        r_squared=round(r_squared, 4),
        n_observations=len(X),
        n_selected=n_selected,
        explanation=explanation,
    )


# ============================================================================
# 특성 엔지니어링
# ============================================================================

def _build_features_and_target(
    prices: list[float],
    vix: list[float],
    fed_rate: float,
    treasury_10y: float,
    dxy_index: float,
) -> tuple[list[str], list[list[float]], list[float]]:
    """
    가격/VIX 시리즈에서 기술적 특성과 20일 전방 수익률 타겟을 구성한다.

    Returns: (feature_names, X_rows, y_values)
    """
    n = len(prices)
    lookbacks = [5, 10, 20, 60]
    max_lookback = 60
    forward = _FORWARD_DAYS

    # 특성 정의
    feature_names = []
    # 가격 수익률 (다중 lookback)
    for lb in lookbacks:
        feature_names.append(f"ret_{lb}d")
    # VIX 관련
    feature_names.extend(["vix_level", "vix_change_5d", "vix_change_20d", "vix_ma_ratio"])
    # 기술 지표
    feature_names.extend(["rsi_14", "momentum_20d", "volatility_20d"])
    # MA 크로스
    feature_names.extend(["price_vs_ma50", "ma50_vs_ma200"])
    # 거시 상수 (있으면)
    if fed_rate > 0 or treasury_10y > 0 or dxy_index > 0:
        feature_names.extend(["yield_spread", "dxy_level"])

    has_macro = fed_rate > 0 or treasury_10y > 0 or dxy_index > 0
    yield_spread = treasury_10y - fed_rate if treasury_10y and fed_rate else 0.0

    X_rows: list[list[float]] = []
    y_values: list[float] = []

    # MA 사전 계산
    ma50 = _rolling_mean(prices, 50)
    ma200 = _rolling_mean(prices, 200) if n >= 200 else _rolling_mean(prices, n)

    for t in range(max_lookback, n - forward):
        row: list[float] = []

        # 가격 수익률
        for lb in lookbacks:
            ret = (prices[t] / prices[t - lb] - 1) * 100
            row.append(ret)

        # VIX
        row.append(vix[t])  # vix_level
        row.append(vix[t] - vix[t - 5] if t >= 5 else 0.0)  # vix_change_5d
        row.append(vix[t] - vix[t - 20] if t >= 20 else 0.0)  # vix_change_20d
        vix_ma20 = sum(vix[t - 19:t + 1]) / 20 if t >= 19 else vix[t]
        row.append(vix[t] / vix_ma20 if vix_ma20 > 0 else 1.0)  # vix_ma_ratio

        # RSI 14
        rsi = _compute_rsi(prices[:t + 1], 14)
        row.append(rsi)

        # 모멘텀 20일
        mom = (prices[t] / prices[t - 20] - 1) * 100
        row.append(mom)

        # 실현 변동성 20일
        rets_20 = [(prices[i] / prices[i - 1] - 1) for i in range(t - 19, t + 1)]
        mean_r = sum(rets_20) / len(rets_20)
        var_r = sum((r - mean_r) ** 2 for r in rets_20) / (len(rets_20) - 1)
        vol = math.sqrt(var_r) * math.sqrt(252) * 100
        row.append(vol)

        # MA 크로스
        row.append((prices[t] / ma50[t] - 1) * 100 if ma50[t] > 0 else 0.0)
        row.append((ma50[t] / ma200[t] - 1) * 100 if ma200[t] > 0 else 0.0)

        # 거시 (상수 — 현재 시점 값을 전체에 적용)
        if has_macro:
            row.append(yield_spread)
            row.append(dxy_index if dxy_index > 0 else 100.0)

        X_rows.append(row)

        # 타겟: 20일 전방 수익률
        fwd_return = (prices[t + forward] / prices[t] - 1) * 100
        y_values.append(fwd_return)

    return feature_names, X_rows, y_values


def _rolling_mean(series: list[float], window: int) -> list[float]:
    """각 시점별 rolling mean (window 미달 시 가용 데이터 평균)."""
    result = []
    for i in range(len(series)):
        start = max(0, i - window + 1)
        result.append(sum(series[start:i + 1]) / (i - start + 1))
    return result


def _compute_rsi(prices: list[float], period: int = 14) -> float:
    """RSI 계산."""
    if len(prices) < period + 1:
        return 50.0
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    recent = deltas[-period * 3:]
    gains = [d if d > 0 else 0.0 for d in recent]
    losses = [-d if d < 0 else 0.0 for d in recent]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ============================================================================
# Fallback (sklearn 없을 때)
# ============================================================================

def _fallback_forecast(
    prices: list[float],
    vix: list[float],
) -> LASSOForecast:
    """sklearn 미설치 시 규칙 기반 대체 예측."""
    ret_20d = (prices[-1] / prices[-20] - 1) * 100 if len(prices) >= 20 else 0.0
    current_vix = vix[-1] if vix else 20.0

    # 단순 모멘텀 + VIX 기반
    pred = ret_20d * 0.3  # 모멘텀 지속 가정 (약화)
    if current_vix > 25:
        pred -= 1.0
    elif current_vix < 15:
        pred += 0.5

    if pred > LASSO_BULLISH_RETURN.value:
        signal = Signal.BULLISH
    elif pred < LASSO_BEARISH_RETURN.value:
        signal = Signal.BEARISH
    else:
        signal = Signal.NEUTRAL

    return LASSOForecast(
        predicted_return=round(pred, 4),
        signal=signal,
        confidence=0.3,  # fallback은 낮은 신뢰도
        key_drivers=(("momentum_20d", round(ret_20d, 4)), ("vix_level", round(current_vix, 2))),
        r_squared=0.0,
        n_observations=0,
        n_selected=0,
        explanation=f"LASSO 불가 (sklearn 미설치). 규칙 기반 대체: 모멘텀 {ret_20d:+.1f}%, VIX {current_vix:.1f}",
    )


# ============================================================================
# 설명 생성
# ============================================================================

def _build_explanation(
    predicted_return: float,
    signal: Signal,
    r_squared: float,
    key_drivers: tuple[tuple[str, float], ...],
    n_observations: int,
    n_selected: int,
    lambda_opt: float,
) -> str:
    """사람이 읽는 LASSO 예측 설명."""
    lines: list[str] = []

    lines.append(f"LASSO 20일 전방 수익률 예측: {predicted_return:+.2f}% → {signal.value}")

    # 모델 품질
    if r_squared > 0.3:
        quality = "양호"
    elif r_squared > 0.15:
        quality = "보통"
    else:
        quality = "낮음 (참고용)"
    lines.append(f"모델 품질: R²={r_squared:.3f} ({quality}), 관측치 {n_observations}개, 선택 변수 {n_selected}개")

    # 주요 동인
    if key_drivers:
        lines.append("주요 동인:")
        for feat, coef in key_drivers:
            direction = "↑" if coef > 0 else "↓"
            feat_label = _feature_label(feat)
            lines.append(f"  {feat_label}: {coef:+.3f} ({direction} 수익률)")

    return "\n".join(lines)


# 특성명 → 한글 라벨 매핑
_FEATURE_LABELS = {
    "ret_5d": "5일 수익률",
    "ret_10d": "10일 수익률",
    "ret_20d": "20일 수익률",
    "ret_60d": "60일 수익률",
    "vix_level": "VIX 수준",
    "vix_change_5d": "VIX 5일 변화",
    "vix_change_20d": "VIX 20일 변화",
    "vix_ma_ratio": "VIX/MA20 비율",
    "rsi_14": "RSI(14)",
    "momentum_20d": "20일 모멘텀",
    "volatility_20d": "20일 변동성",
    "price_vs_ma50": "가격/MA50 괴리",
    "ma50_vs_ma200": "MA50/MA200 괴리",
    "yield_spread": "수익률 곡선 스프레드",
    "dxy_level": "달러 인덱스",
}


def _feature_label(name: str) -> str:
    return _FEATURE_LABELS.get(name, name)
