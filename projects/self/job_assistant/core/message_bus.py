"""
Job Assistant — 경량화 메시지 버스
autoai/message_bus.py에서 핵심만 추출 (큐 기반 제거, 단순 컨텍스트 패싱)

경량화 내역:
- 제거: AgentRole enum (autoai 전용 역할), MessageBus 큐/스레드, 콜백 시스템
- 유지: Message 데이터 포맷, TaskContext, JSON 직렬화
- 이유: job_assistant는 순차 파이프라인 (search→analyze→write), 큐 불필요
"""
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)


class MessageType(Enum):
    TASK = "task"
    RESULT = "result"
    STATUS = "status"
    ERROR = "error"


@dataclass
class Message:
    """에이전트 간 메시지 포맷"""
    msg_type: MessageType
    sender: str
    receiver: str
    content: Any
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    task_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["msg_type"] = self.msg_type.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


@dataclass
class JobContext:
    """에이전트 파이프라인 전체 공유 컨텍스트"""
    task_id: str
    company: str
    role: str
    url: str = ""
    search_result: Optional[Dict] = None
    job_posting: Optional[Any] = None       # JobPosting
    analysis: Optional[Any] = None          # Analysis
    collected_content: Optional[Any] = None # CollectedContent (CollectorAgent)
    summarized_sources: Optional[Any] = None# List[SummarizedSource] (SummarizerAgent)
    notebook_result: Optional[Any] = None   # NotebookResult (NotebookPublisher)
    cover_letters_raw: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)

    def add_message(self, sender: str, receiver: str,
                    content: Any, msg_type: MessageType = MessageType.RESULT):
        msg = Message(
            msg_type=msg_type,
            sender=sender,
            receiver=receiver,
            content=content,
            task_id=self.task_id,
        )
        self.messages.append(msg)
        return msg

    def to_summary(self) -> str:
        return (
            f"Task: {self.task_id}\n"
            f"Company: {self.company} / Role: {self.role}\n"
            f"Search done: {self.search_result is not None}\n"
            f"Posting parsed: {self.job_posting is not None}\n"
            f"Analysis done: {self.analysis is not None}\n"
            f"Cover letters loaded: {list(self.cover_letters_raw.keys())}\n"
            f"Errors: {len(self.errors)}"
        )
