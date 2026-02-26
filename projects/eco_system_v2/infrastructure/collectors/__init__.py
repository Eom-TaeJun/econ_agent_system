# infrastructure/collectors
from .yfinance_collector import collect_market
from .fred_collector import collect_fed_rate

__all__ = ["collect_market", "collect_fed_rate"]
