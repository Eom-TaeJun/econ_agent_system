"""
ProfileAnalyzer — 프로필 분석 → 검색 파라미터 생성
Claude API로 profile.md를 분석해 DiscoveryAgent가 쓸 파라미터를 생성한다.
"""
import json
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List

import anthropic

from config import API_CONFIG, MODELS


@dataclass
class ProfileSearchConfig:
    """ProfileAnalyzer가 생성하는 검색 파라미터"""
    role_keywords: List[str]
    target_companies: List[str]
    company_keywords: List[str]
    exclude_requirements: List[str]
    career_level: str = "신입"


class ProfileAnalyzer:
    SYSTEM_PROMPT = """당신은 채용 전략 전문가입니다.
지원자의 프로필을 분석해 현재 한국 취업 시장에서 맞는 직무와 기업을 추론합니다.
반드시 JSON만 반환하세요. 다른 텍스트 없이."""

    USER_PROMPT_TEMPLATE = """아래는 지원자 프로필입니다.
오늘 날짜: {today}

{profile_text}

---
위 프로필을 분석해 아래 JSON 형식으로 반환하세요:
{{
  "role_keywords": ["직무 키워드1", "직무 키워드2", ...],
  "target_companies": ["회사명1", "회사명2", ...],
  "company_keywords": ["업종 키워드1", "업종 키워드2", ...],
  "exclude_requirements": ["제외조건1", "제외조건2", ...]
}}

규칙:
- role_keywords: 사람인/원티드 검색창에 입력할 직무 키워드 5~10개 (한국어)
- target_companies: 이 프로필에 맞는 구체적 회사명 10~20개 (한국 기업)
- company_keywords: 사람인 검색에 쓸 업종/기업유형 키워드 3~5개
- exclude_requirements: 공고 요건 텍스트에서 제외할 키워드들
- 오늘 날짜 기준 현재 채용 중이거나 곧 채용할 가능성 높은 기업 우선"""

    def __init__(self):
        self.logger = logging.getLogger("ProfileAnalyzer")
        self.client = anthropic.Anthropic(api_key=API_CONFIG.anthropic_key)

    def analyze(self, profile_path: str) -> ProfileSearchConfig:
        profile_text = Path(profile_path).read_text(encoding="utf-8")
        prompt = self.USER_PROMPT_TEMPLATE.format(
            today=date.today().isoformat(),
            profile_text=profile_text,
        )

        self.logger.info("프로필 분석 중...")
        message = self.client.messages.create(
            model=MODELS["anthropic"],
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            system=self.SYSTEM_PROMPT,
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:-1])
        data = json.loads(raw)

        return ProfileSearchConfig(
            role_keywords=data.get("role_keywords", []),
            target_companies=data.get("target_companies", []),
            company_keywords=data.get("company_keywords", []),
            exclude_requirements=data.get("exclude_requirements", []),
            career_level=data.get("career_level", "신입"),
        )
