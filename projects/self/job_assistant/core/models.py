"""
Job Assistant — 핵심 데이터 모델
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class JobPosting:
    """채용공고 구조화 모델"""
    company: str
    role: str
    vision: str                   # 회사 비전/미션
    jd: str                       # Job Description 전문
    requirements: List[str]       # 필수 자격요건
    preferred: List[str]          # 우대사항
    recent_work: str              # 현업에서 실제로 하는 일
    source_url: str = ""          # 공고 URL (있을 경우)
    raw_search: str = ""          # Perplexity 원문 (디버깅용)


@dataclass
class Analysis:
    """AnalyzerAgent가 생성하는 분석 결과"""
    posting: JobPosting
    key_competencies: List[str]   # 채용에서 가장 중요한 핵심 역량
    technical_skills: List[str]   # 기술 스킬 (언어, 프레임워크 등)
    soft_skills: List[str]        # 소프트 스킬 (협업, 커뮤니케이션 등)
    culture_fit: str              # 조직문화 / 인재상
    keywords: List[str]           # 자소서에서 강조해야 할 키워드
    cover_letter_sections: List[str]  # 예상 자소서 항목명


@dataclass
class CoverLetterSection:
    """자소서 한 항목에 대한 매핑 결과"""
    title: str                    # 항목명 (지원동기, 직무역량 등)
    source: str                   # 기존 자소서에서 재사용할 내용
    tailored: str                 # 이 기업에 맞게 조정한 방향
    gap: str                      # 부족한 부분 / 추가 필요 내용
    task_file: Optional[str] = None  # 병렬 처리 task 파일 경로


@dataclass
class CollectedContent:
    """CollectorAgent가 카테고리별로 수집한 원문"""
    company: str
    role: str
    # 카테고리: JD / COMPANY / INSIDER / SUCCESS
    raw: dict = field(default_factory=dict)
    sources_used: List[str] = field(default_factory=list)
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SummarizedSource:
    """NotebookLM에 올릴 소스 1개"""
    title: str           # 노트북 소스 제목
    content: str         # 업로드할 텍스트 본문
    category: str        # JD / COMPANY / INSIDER / SUCCESS / PROFILE
    model_used: str      # 어떤 모델로 요약했는지


@dataclass
class NotebookResult:
    """NotebookPublisher 결과 — 생성된 소스 목록 + 저장 경로"""
    company: str
    role: str
    sources: List[SummarizedSource] = field(default_factory=list)
    output_dir: str = ""        # 소스 파일 저장 경로
    notebook_id: str = ""       # MCP로 생성 후 채워짐
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CoverLetterResult:
    """WriterAgent의 최종 결과물"""
    company: str
    role: str
    sections: List[CoverLetterSection] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    cover_letters_used: List[str] = field(default_factory=list)  # 사용된 자소서 파일명

    def has_gaps(self) -> bool:
        return any(s.gap for s in self.sections)

    def pending_tasks(self) -> List[str]:
        return [s.task_file for s in self.sections if s.task_file]
