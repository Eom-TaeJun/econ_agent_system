"""
Job Assistant — API 키 및 모델 설정
환경변수에서 API 키 로드
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class APIConfig:
    anthropic_key: Optional[str] = None
    perplexity_key: Optional[str] = None
    openai_key: Optional[str] = None
    gemini_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> "APIConfig":
        return cls(
            anthropic_key=os.getenv("ANTHROPIC_API_KEY"),
            perplexity_key=os.getenv("PERPLEXITY_API_KEY"),
            openai_key=os.getenv("OPENAI_API_KEY"),
            gemini_key=os.getenv("GEMINI_API_KEY"),
        )

    def validate(self) -> dict:
        return {
            "anthropic": bool(self.anthropic_key),
            "perplexity": bool(self.perplexity_key),
            "openai": bool(self.openai_key),
            "gemini": bool(self.gemini_key),
        }

    def check_required(self):
        """필수 키(anthropic, perplexity) 누락 시 에러"""
        required = ["anthropic", "perplexity"]
        missing = [k for k in required if not getattr(self, f"{k}_key")]
        if missing:
            raise EnvironmentError(
                f"API 키 누락: {', '.join(missing)}\n"
                "export ANTHROPIC_API_KEY=...\n"
                "export PERPLEXITY_API_KEY=..."
            )


# 모델 설정
# - anthropic: 맥락 추론, fit 분석
# - perplexity: 실시간 웹 검색
# - openai: 긴 원문 압축 (빠르고 저렴)
# - gemini: 패턴 추출 (면접 질문 공통점 등)
MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "anthropic_fast": "claude-haiku-4-5-20251001",
    "perplexity": "sonar-pro",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
COVER_LETTERS_DIR = os.path.join(DATA_DIR, "cover_letters")
OUTPUTS_DIR = os.path.join(DATA_DIR, "outputs")
TASKS_PENDING_DIR = os.path.join(DATA_DIR, "tasks", "pending")
TASKS_DONE_DIR = os.path.join(DATA_DIR, "tasks", "done")

API_CONFIG = APIConfig.from_env()
