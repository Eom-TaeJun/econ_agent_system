"""
infrastructure/profile_loader.py

job_assistant의 Analysis JSON을 읽어 eco_system_v2 에이전트용 context 문자열로 변환.

사용법:
    from infrastructure.profile_loader import load_profile, ProfileData

    profile = load_profile("/path/to/웨이브릿지_퀀트리서처_2026-02-26_analysis.json")
    context_str = profile.to_context()
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ProfileData:
    """job_assistant Analysis JSON의 도메인 표현"""
    company: str
    role: str
    vision: str = ""
    recent_work: str = ""
    key_competencies: list[str] = field(default_factory=list)
    technical_skills: list[str] = field(default_factory=list)
    soft_skills: list[str] = field(default_factory=list)
    culture_fit: str = ""
    keywords: list[str] = field(default_factory=list)
    cover_letter_sections: list[str] = field(default_factory=list)

    def to_context(self) -> str:
        """에이전트 프롬프트에 삽입할 context 문자열 생성"""
        lines = [
            f"[분석 대상] {self.company} | {self.role}",
        ]
        if self.key_competencies:
            lines.append(f"[핵심 역량] {', '.join(self.key_competencies)}")
        if self.technical_skills:
            lines.append(f"[기술 스킬] {', '.join(self.technical_skills)}")
        if self.keywords:
            lines.append(f"[핵심 키워드] {', '.join(self.keywords)}")
        if self.recent_work:
            lines.append(f"[현업 업무] {self.recent_work[:200]}")
        if self.culture_fit:
            lines.append(f"[조직문화] {self.culture_fit[:150]}")
        lines.append(
            f"\n위 직무 관점에서 현재 거시경제 신호가 {self.company}의 사업과 "
            f"{self.role} 직무에 어떤 의미를 갖는지 분석해줘."
        )
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "company": self.company,
            "role": self.role,
            "key_competencies": self.key_competencies,
            "technical_skills": self.technical_skills,
            "keywords": self.keywords,
            "culture_fit": self.culture_fit,
        }


def load_profile(path: str) -> ProfileData:
    """
    job_assistant Analysis JSON 파일을 읽어 ProfileData 반환.

    파일이 없거나 파싱 실패 시 ValueError.
    """
    p = Path(path)
    if not p.exists():
        raise ValueError(f"프로필 파일 없음: {path}")

    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 파싱 실패: {path} — {e}") from e

    company = data.get("company", "")
    role = data.get("role", "")
    if not company or not role:
        raise ValueError(f"company/role 필드 없음: {path}")

    profile = ProfileData(
        company=company,
        role=role,
        vision=data.get("vision", ""),
        recent_work=data.get("recent_work", ""),
        key_competencies=data.get("key_competencies", []),
        technical_skills=data.get("technical_skills", []),
        soft_skills=data.get("soft_skills", []),
        culture_fit=data.get("culture_fit", ""),
        keywords=data.get("keywords", []),
        cover_letter_sections=data.get("cover_letter_sections", []),
    )

    logger.info(f"[profile_loader] 로드 완료: {company} / {role}")
    return profile
