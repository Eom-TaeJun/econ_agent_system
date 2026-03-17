"""
domain/report.py — ReportSection, AnalysisReport Value Objects

규칙: 이 파일은 stdlib 외 import 금지 (anthropic, httpx, yfinance 등 절대 금지).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ReportSection:
    """리포트 섹션 — Value Object (불변)."""

    title: str
    content: str
    order: int = 0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "content": self.content,
            "order": self.order,
        }


@dataclass(frozen=True)
class AnalysisReport:
    """
    최종 분석 리포트 — Value Object (불변).

    title: 리포트 제목
    summary: 핵심 요약 (1-2문장)
    sections: 리포트 섹션 목록
    generated_at: 생성 시각 ISO 8601
    """

    title: str
    summary: str
    sections: tuple[ReportSection, ...] = ()
    generated_at: str = ""

    def __post_init__(self) -> None:
        if not self.generated_at:
            object.__setattr__(self, "generated_at", datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "summary": self.summary,
            "sections": [s.to_dict() for s in self.sections],
            "generated_at": self.generated_at,
        }

    def to_markdown(self) -> str:
        lines = [f"# {self.title}", "", f"> {self.summary}", ""]
        for section in sorted(self.sections, key=lambda s: s.order):
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")
        lines.append(f"---\n*Generated at {self.generated_at} by eco_system_v2*")
        return "\n".join(lines)
