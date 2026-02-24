"""
Job Assistant — 경량화 BaseAgent
autoai/base_agent.py에서 핵심만 추출

경량화 내역:
- 제거: AgentRegistry, MessageBus 큐 send/receive, checkpoint (user interrupt)
- 유지: 로깅 헬퍼, _setup_client 추상메서드, process 추상메서드
- 이유: 단순 순차 파이프라인이므로 레지스트리/큐 불필요
"""
import logging
from abc import ABC, abstractmethod
from typing import Any

from core.message_bus import JobContext


class BaseAgent(ABC):
    """모든 에이전트의 추상 기반 클래스"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_client()

    @abstractmethod
    def _setup_client(self):
        """API 클라이언트 초기화"""
        pass

    @abstractmethod
    def run(self, context: JobContext) -> Any:
        """컨텍스트를 받아 처리하고 결과 반환"""
        pass

    def log_progress(self, msg: str):
        self.logger.info(f"[{self.name}] {msg}")

    def log_success(self, msg: str):
        self.logger.info(f"[{self.name}] OK — {msg}")

    def log_error(self, msg: str):
        self.logger.error(f"[{self.name}] ERR — {msg}")
