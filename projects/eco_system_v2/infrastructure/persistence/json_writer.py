"""
infrastructure/persistence/json_writer.py

분석 결과를 JSON 파일로 저장.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def write(result: dict, output_dir: str = "outputs") -> str:
    """
    result dict를 JSON으로 저장.

    파일명: {output_dir}/eco_{date}_{short_id}.json
    반환: 저장된 파일 경로
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    date_str = result.get("date", "unknown")
    short_id = os.urandom(3).hex()  # 6자리 hex
    filename = f"eco_{date_str}_{short_id}.json"
    filepath = str(Path(output_dir) / filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"[json_writer] 저장 완료: {filepath}")
    return filepath
