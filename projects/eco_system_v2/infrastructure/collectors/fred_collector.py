"""
infrastructure/collectors/fred_collector.py

FRED API로 연방기금금리 수집.
FRED_API_KEY 환경변수 필요.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def collect_fed_rate(lookback_days: int = 90) -> float:
    """
    FRED에서 Fed Funds Rate (FEDFUNDS) 수집.

    실패 시 0.0 반환 (fail-soft).
    """
    api_key = os.getenv("FRED_API_KEY", "")
    if not api_key:
        logger.warning("[fred] FRED_API_KEY 환경변수 없음 — fed_rate=0.0 반환")
        return 0.0

    start = datetime.today() - timedelta(days=lookback_days)

    try:
        from fredapi import Fred

        fred = Fred(api_key=api_key)
        series = fred.get_series("FEDFUNDS", observation_start=start)
        if series.empty:
            return 0.0
        rate = float(series.iloc[-1])
        logger.info(f"[fred] Fed Funds Rate={rate:.2f}%")
        return rate
    except Exception as e:
        logger.warning(f"[fred] FRED 수집 실패: {e}")
        return 0.0
