"""
agents/base.py — BaseAgent

모든 에이전트의 베이스 클래스.
- async execute() 추상 메서드
- run()에서 재시도 + asyncio.wait_for 타임아웃 처리

규칙: BaseAgent를 상속하지 않은 에이전트는 Orchestrator에 등록 불가.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod

from domain.signal import EconomicSignal
from domain.market_data import MarketData

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    에이전트 Bounded Context의 공통 인터페이스.

    name: 에이전트 식별자 (로그, 합의 결과에 사용)
    max_retries: execute() 실패 시 최대 재시도 횟수
    timeout_sec: 단일 시도 타임아웃 (초)
    """

    def __init__(
        self,
        name: str,
        max_retries: int = 2,
        timeout_sec: float = 30.0,
    ) -> None:
        self.name = name
        self.max_retries = max_retries
        self.timeout_sec = timeout_sec

    @abstractmethod
    async def execute(self, market_data: MarketData, context: str = "") -> EconomicSignal:
        """에이전트 핵심 로직. 서브클래스에서 구현."""
        ...

    async def run(self, market_data: MarketData, context: str = "") -> EconomicSignal:
        """재시도 + 타임아웃 래퍼"""
        last_exc: Exception = RuntimeError(f"[{self.name}] 알 수 없는 오류")

        for attempt in range(1, self.max_retries + 1):
            try:
                return await asyncio.wait_for(
                    self.execute(market_data, context),
                    timeout=self.timeout_sec,
                )
            except asyncio.TimeoutError:
                last_exc = TimeoutError(
                    f"[{self.name}] attempt {attempt} timed out ({self.timeout_sec}s)"
                )
                logger.warning(str(last_exc))
            except Exception as e:
                last_exc = e
                logger.warning(f"[{self.name}] attempt {attempt} failed: {e}")

            if attempt < self.max_retries:
                await asyncio.sleep(1.0)

        raise last_exc
