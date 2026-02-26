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
