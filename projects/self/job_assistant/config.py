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

    @classmethod
    def from_env(cls) -> "APIConfig":
        return cls(
            anthropic_key=os.getenv("ANTHROPIC_API_KEY"),
            perplexity_key=os.getenv("PERPLEXITY_API_KEY"),
        )

    def validate(self) -> dict:
        status = {
            "anthropic": bool(self.anthropic_key),
            "perplexity": bool(self.perplexity_key),
        }
        return status

    def check_required(self):
        """필수 키 누락 시 에러"""
        missing = [name for name, ok in self.validate().items() if not ok]
        if missing:
            raise EnvironmentError(
                f"API 키 누락: {', '.join(missing)}\n"
                "export ANTHROPIC_API_KEY=...\n"
                "export PERPLEXITY_API_KEY=..."
            )


MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "perplexity": "llama-3.1-sonar-large-128k-online",
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
COVER_LETTERS_DIR = os.path.join(DATA_DIR, "cover_letters")
OUTPUTS_DIR = os.path.join(DATA_DIR, "outputs")
TASKS_PENDING_DIR = os.path.join(DATA_DIR, "tasks", "pending")
TASKS_DONE_DIR = os.path.join(DATA_DIR, "tasks", "done")

API_CONFIG = APIConfig.from_env()
