"""
infrastructure/collectors/yfinance_collector.py

yfinance로 VIX, S&P500 데이터 수집 → MarketData(domain) 반환.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from domain.market_data import MarketData

logger = logging.getLogger(__name__)


def collect_market(lookback_days: int = 90) -> MarketData:
    """
    VIX와 S&P500 데이터 수집.

    실패 시 zero-value MarketData 반환 (fail-soft).
    """
    end = datetime.today()
    start = end - timedelta(days=lookback_days)

    vix_current = 0.0
    vix_30d_avg = 0.0
    spx_return_30d = 0.0

    try:
        import yfinance as yf

        vix = yf.Ticker("^VIX").history(start=start, end=end)
        spx = yf.Ticker("^GSPC").history(start=start, end=end)

        if not vix.empty:
            vix_current = float(vix["Close"].iloc[-1])
            vix_30d_avg = float(vix["Close"].tail(22).mean())
            logger.info(f"[yfinance] VIX={vix_current:.1f}, 30d avg={vix_30d_avg:.1f}")

        if not spx.empty and len(spx) >= 22:
            spx_return_30d = float(
                (spx["Close"].iloc[-1] / spx["Close"].iloc[-22] - 1) * 100
            )
            logger.info(f"[yfinance] SPX 30d return={spx_return_30d:+.1f}%")

    except Exception as e:
        logger.warning(f"[yfinance] 수집 실패 (yfinance 미설치?): {e}")

    return MarketData(
        vix_current=vix_current,
        vix_30d_avg=vix_30d_avg,
        spx_return_30d=spx_return_30d,
    )


def collect_extended_market(lookback_days: int = 252) -> dict[str, list[float]]:
    """
    레짐/리스크 분석용 확장 시장 데이터 수집.

    Returns:
        {
            "spx_prices": [float, ...],   # SPX 일봉 종가
            "vix_prices": [float, ...],   # VIX 일봉 종가
            "treasury_10y": float,        # 10년물 수익률
            "dxy_index": float,           # 달러 인덱스
            "gold_price": float,          # 금 가격
        }
    """
    end = __import__("datetime").datetime.today()
    start = end - __import__("datetime").timedelta(days=lookback_days)

    result: dict[str, object] = {
        "spx_prices": [],
        "vix_prices": [],
        "treasury_10y": 0.0,
        "dxy_index": 0.0,
        "gold_price": 0.0,
    }

    try:
        import yfinance as yf

        # SPX 가격 시리즈
        spx = yf.Ticker("^GSPC").history(start=start, end=end)
        if not spx.empty:
            result["spx_prices"] = [float(p) for p in spx["Close"].tolist()]

        # VIX 시리즈
        vix = yf.Ticker("^VIX").history(start=start, end=end)
        if not vix.empty:
            result["vix_prices"] = [float(p) for p in vix["Close"].tolist()]

        # 10년물 국채 수익률
        tny = yf.Ticker("^TNX").history(period="5d")
        if not tny.empty:
            result["treasury_10y"] = float(tny["Close"].iloc[-1])

        # DXY 달러 인덱스 (DX=F: 달러 인덱스 선물)
        dxy = yf.Ticker("DX=F").history(period="5d")
        if not dxy.empty:
            result["dxy_index"] = float(dxy["Close"].iloc[-1])

        # 금 가격
        gold = yf.Ticker("GC=F").history(period="5d")
        if not gold.empty:
            result["gold_price"] = float(gold["Close"].iloc[-1])

        logger.info(
            f"[yfinance] extended: SPX {len(result['spx_prices'])}일, "
            f"10Y={result['treasury_10y']:.2f}%, "
            f"DXY={result['dxy_index']:.1f}, "
            f"Gold=${result['gold_price']:.0f}"
        )

    except Exception as e:
        logger.warning(f"[yfinance] extended 수집 실패: {e}")

    return result
