"""
config.py — API 키, 모델명, 경로 설정

환경변수에서 읽음. .env 파일 지원 (python-dotenv 선택적).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv() -> None:
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    except ImportError:
        pass  # python-dotenv 미설치 시 무시


_load_dotenv()


@dataclass
class Config:
    # API 키
    ANTHROPIC_API_KEY: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    PERPLEXITY_API_KEY: str = field(
        default_factory=lambda: os.getenv("PERPLEXITY_API_KEY", "")
    )
    FRED_API_KEY: str = field(
        default_factory=lambda: os.getenv("FRED_API_KEY", "")
    )

    # 모델명
    CLAUDE_MODEL: str = field(
        default_factory=lambda: os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    )
    PERPLEXITY_MODEL: str = field(
        default_factory=lambda: os.getenv("PERPLEXITY_MODEL", "sonar")
    )

    # 경로
    OUTPUT_DIR: str = field(
        default_factory=lambda: os.getenv("OUTPUT_DIR", "outputs")
    )

    def validate(self, quick: bool = False) -> None:
        """필수 키 검증. quick 모드는 ANTHROPIC_API_KEY만 필요."""
        if not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY 환경변수 없음")
        if not quick and not self.PERPLEXITY_API_KEY:
            raise ValueError("full 모드에는 PERPLEXITY_API_KEY 필요 (또는 --quick 사용)")


# 싱글턴
config = Config()
