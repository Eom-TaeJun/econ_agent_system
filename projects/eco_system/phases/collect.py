"""
eco_system Phase 1: 데이터 수집
profile을 받아 tickers, sources, lookback_days를 동적으로 결정
"""

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# source 플래그별 추가 티커
SOURCE_TICKERS = {
    "crypto":       ["BTC-USD", "ETH-USD"],
    "korea":        ["^KS11", "^KQ11"],           # KOSPI, KOSDAQ
    "alternatives": ["GLD", "USO", "DBC", "VNQ"],
}

# source 플래그별 FRED 시리즈
FRED_SERIES = {
    "macro":  ["FEDFUNDS", "DGS10", "DGS2", "T10Y2Y"],
    "credit": ["BAMLH0A0HYM2", "BAMLC0A0CM"],     # HY / IG 스프레드
}


def collect(profile: dict | None = None) -> dict[str, Any]:
    """
    프로필 기반 시장 데이터 수집.
    profile 없으면 base 기본값으로 동작.
    """
    if profile is None:
        profile = {}

    cfg = profile.get("data", {})
    lookback_days: int = cfg.get("lookback_days", 90)
    sources: dict = cfg.get("sources", {})
    tickers_cfg: dict = cfg.get("tickers", {})

    # 수집할 티커 목록 구성 (프로필 섹션 전부 합침)
    tickers: list[str] = []
    for section in ("core", "extra", "sectors", "factors", "fx", "commodities"):
        tickers += tickers_cfg.get(section, [])

    # source 플래그에 따른 추가 티커
    for source_key, extra in SOURCE_TICKERS.items():
        if sources.get(source_key, False):
            tickers += extra

    # 기본 티커 fallback (프로필 없을 때)
    if not tickers:
        tickers = ["^VIX", "^GSPC", "SPY", "TLT", "HYG"]

    tickers = list(dict.fromkeys(tickers))  # 중복 제거, 순서 유지

    end = datetime.today()
    start = end - timedelta(days=lookback_days)
    data: dict[str, Any] = {}

    # ── yfinance 배치 수집 ─────────────────────────────────────
    try:
        import yfinance as yf
        raw = yf.download(tickers, start=start, end=end, progress=False, auto_adjust=True)
        close = raw["Close"] if "Close" in raw.columns else raw

        for ticker in tickers:
            key = ticker.replace("^", "").replace("-", "_").lower()
            col = close[ticker] if ticker in close.columns else None
            if col is None:
                continue
            series = col.dropna()
            if series.empty:
                continue
            data[f"{key}_current"] = float(series.iloc[-1])
            # 22 거래일 ≈ 30 영업일 (연 252 거래일 / 12개월)
            # 관례: 월간 수익률 산출 시 달력일이 아닌 거래일 기준
            if len(series) >= 22:
                data[f"{key}_return_30d"] = float(
                    (series.iloc[-1] / series.iloc[-22] - 1) * 100
                )
            # 5 거래일 = 1주일 단기 평균 (일간 노이즈 평활)
            if len(series) >= 5:
                data[f"{key}_5d_avg"] = float(series.tail(5).mean())

        logger.info(f"[collect] yfinance 완료: {len(tickers)}개 티커")
    except Exception as e:
        logger.warning(f"[collect] yfinance 실패: {e}")

    # ── FRED 수집 ──────────────────────────────────────────────
    active_fred: list[str] = []
    for source_key, series_ids in FRED_SERIES.items():
        if sources.get(source_key, True):   # macro/credit 기본 ON
            active_fred += series_ids

    if active_fred:
        try:
            import os
            from fredapi import Fred
            fred = Fred(api_key=os.getenv("FRED_API_KEY", ""))
            for sid in active_fred:
                try:
                    s = fred.get_series(sid, observation_start=start)
                    if not s.empty:
                        data[sid.lower()] = float(s.dropna().iloc[-1])
                except Exception:
                    pass
            logger.info(f"[collect] FRED 완료: {active_fred}")
        except Exception as e:
            logger.warning(f"[collect] FRED 실패: {e}")

    data["collected_at"] = datetime.now().isoformat()
    data["_profile"] = profile.get("name", "base")
    data["_tickers_count"] = len(tickers)
    return data
