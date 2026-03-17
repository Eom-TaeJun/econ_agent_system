"""
domain/allocation.py — 자산 배분 추천 Value Objects

레짐 + 신호 + 리스크 기반 전략적 자산 배분.

규칙: 이 파일은 stdlib 외 import 금지.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AssetClass(str, Enum):
    """자산 클래스."""
    EQUITY = "equity"     # 주식
    BOND = "bond"         # 채권
    GOLD = "gold"         # 금
    CASH = "cash"         # 현금


@dataclass(frozen=True)
class AllocationAdjustment:
    """배분 조정 하나의 기록 (투명성용)."""

    source: str           # 조정 원인 (regime, signal, risk, lasso)
    asset: AssetClass
    delta: float          # 변화량 (±%)
    reason: str           # 사유

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "asset": self.asset.value,
            "delta": round(self.delta, 2),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class AllocationResult:
    """자산 배분 추천 결과."""

    allocations: tuple[tuple[str, float], ...]           # (asset_class, weight)
    strategy_name: str                                   # 전략명
    adjustments: tuple[AllocationAdjustment, ...]        # 조정 이력
    rationale: str                                       # 종합 설명

    def to_dict(self) -> dict:
        return {
            "allocations": {k: round(v, 2) for k, v in self.allocations},
            "strategy_name": self.strategy_name,
            "adjustments": [a.to_dict() for a in self.adjustments],
            "rationale": self.rationale,
        }
