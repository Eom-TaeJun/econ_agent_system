"""
domain/market_data.py — MarketData Value Object

규칙: 이 파일은 stdlib 외 import 금지 (anthropic, httpx, yfinance 등 절대 금지).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class MarketData:
    """
    수집된 거시경제 데이터 스냅샷 — Value Object (불변).

    vix_current: 현재 VIX 지수
    vix_30d_avg: 30일 VIX 평균
    spx_return_30d: S&P500 30일 수익률 (%)
    fed_rate: 연방기금금리 (%)
    collected_at: 수집 시각 ISO 8601
    """

    vix_current: float = 0.0
    vix_30d_avg: float = 0.0
    spx_return_30d: float = 0.0
    fed_rate: float = 0.0
    treasury_10y: float = 0.0
    treasury_2y: float = 0.0
    dxy_index: float = 0.0
    gold_price: float = 0.0
    oil_price: float = 0.0
    copper_price: float = 0.0
    hyg_price: float = 0.0       # High Yield ETF (신용 위험 프록시)
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def yield_spread_10y_2y(self) -> float:
        """10Y-2Y 수익률 스프레드 (역전 시 음수)."""
        if self.treasury_10y and self.treasury_2y:
            return self.treasury_10y - self.treasury_2y
        return 0.0

    @property
    def yield_spread_10y_ffr(self) -> float:
        """10Y-FFR 수익률 스프레드."""
        if self.treasury_10y and self.fed_rate:
            return self.treasury_10y - self.fed_rate
        return 0.0

    def to_prompt_context(self) -> str:
        """에이전트 프롬프트에 삽입할 텍스트 요약"""
        parts = [
            f"VIX: {self.vix_current:.1f} (30d avg {self.vix_30d_avg:.1f})",
            f"S&P500 30d return: {self.spx_return_30d:+.1f}%",
            f"Fed Funds Rate: {self.fed_rate:.2f}%",
        ]
        if self.treasury_10y:
            parts.append(f"10Y Treasury: {self.treasury_10y:.2f}%")
        if self.treasury_2y:
            parts.append(f"2Y Treasury: {self.treasury_2y:.2f}%")
            if self.treasury_10y:
                parts.append(f"10Y-2Y spread: {self.yield_spread_10y_2y:+.2f}%")
        if self.dxy_index:
            parts.append(f"DXY: {self.dxy_index:.1f}")
        if self.gold_price:
            parts.append(f"Gold: ${self.gold_price:.0f}")
        if self.oil_price:
            parts.append(f"Oil(WTI): ${self.oil_price:.1f}")
        if self.copper_price:
            parts.append(f"Copper: ${self.copper_price:.2f}")
        if self.hyg_price:
            parts.append(f"HYG: ${self.hyg_price:.1f}")
        return ", ".join(parts)

    def to_dict(self) -> dict:
        d = {
            "vix_current": self.vix_current,
            "vix_30d_avg": self.vix_30d_avg,
            "spx_return_30d": self.spx_return_30d,
            "fed_rate": self.fed_rate,
            "treasury_10y": self.treasury_10y,
            "treasury_2y": self.treasury_2y,
            "dxy_index": self.dxy_index,
            "gold_price": self.gold_price,
            "oil_price": self.oil_price,
            "copper_price": self.copper_price,
            "hyg_price": self.hyg_price,
            "collected_at": self.collected_at,
        }
        # 파생 지표
        if self.treasury_10y and self.treasury_2y:
            d["yield_spread_10y_2y"] = round(self.yield_spread_10y_2y, 4)
        if self.treasury_10y and self.fed_rate:
            d["yield_spread_10y_ffr"] = round(self.yield_spread_10y_ffr, 4)
        return d
