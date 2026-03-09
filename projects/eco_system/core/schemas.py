"""
eco_system core schemas — EIMAS 스키마를 참조해 경량화
출처: ~/projects/autoai/eimas/core/schemas.py
"""

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime
from enum import Enum


class Signal(str, Enum):
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    GUARDRAIL = "guardrail"


@dataclass
class AgentRequest:
    task: str
    data: dict[str, Any] = field(default_factory=dict)
    context: str = ""


@dataclass
class AgentResponse:
    agent: str
    signal: Signal
    confidence: float          # 0.0 ~ 1.0
    rationale: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "signal": self.signal.value,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "timestamp": self.timestamp,
        }


@dataclass
class EcoResult:
    """전체 파이프라인 최종 결과"""
    date: str
    consensus_signal: Signal
    consensus_confidence: float
    agent_responses: list[AgentResponse] = field(default_factory=list)
    key_factors: list[str] = field(default_factory=list)
    summary: str = ""
    guardrail_notes: str = ""           # GuardrailAgent 검증 메모
    extras: dict[str, Any] = field(default_factory=dict)  # 프로필별 추가 데이터

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "consensus_signal": self.consensus_signal.value,
            "consensus_confidence": self.consensus_confidence,
            "agent_responses": [r.to_dict() for r in self.agent_responses],
            "key_factors": self.key_factors,
            "summary": self.summary,
            "guardrail_notes": self.guardrail_notes,
            "extras": self.extras,
        }
