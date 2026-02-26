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
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_prompt_context(self) -> str:
        """에이전트 프롬프트에 삽입할 텍스트 요약"""
        return (
            f"VIX: {self.vix_current:.1f} (30d avg {self.vix_30d_avg:.1f}), "
            f"S&P500 30d return: {self.spx_return_30d:+.1f}%, "
            f"Fed Funds Rate: {self.fed_rate:.2f}%"
        )

    def to_dict(self) -> dict:
        return {
            "vix_current": self.vix_current,
            "vix_30d_avg": self.vix_30d_avg,
            "spx_return_30d": self.spx_return_30d,
            "fed_rate": self.fed_rate,
            "collected_at": self.collected_at,
        }
