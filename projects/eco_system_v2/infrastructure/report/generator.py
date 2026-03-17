"""
infrastructure/report/generator.py

Claude API로 EcoResult → AnalysisReport 생성.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from functools import partial

from domain.report import AnalysisReport, ReportSection

logger = logging.getLogger(__name__)

_JSON_PATTERN = re.compile(r"\{.*\}", re.DOTALL)

_REPORT_TEMPLATE = """\
다음 거시경제 분석 결과를 바탕으로 구조화된 투자 리포트를 작성해줘.

분석 결과:
{result_json}

다음 섹션을 포함하는 리포트를 JSON으로 반환해:
{{
  "title": "<리포트 제목>",
  "summary": "<핵심 요약 1-2문장>",
  "sections": [
    {{"title": "시장 개요", "content": "<현재 시장 상황 요약>"}},
    {{"title": "에이전트 분석 요약", "content": "<에이전트별 판단 비교>"}},
    {{"title": "레짐 및 리스크", "content": "<레짐/리스크 해석>"}},
    {{"title": "투자 시사점", "content": "<구체적 액션 포인트>"}},
    {{"title": "리스크 요인", "content": "<주시해야 할 리스크>"}}
  ]
}}"""


async def generate_report(
    result_dict: dict,
    api_key: str,
    model: str = "claude-sonnet-4-6",
) -> AnalysisReport:
    """
    EcoResult.to_dict()를 Claude로 전달해 구조화 리포트를 생성한다.

    Returns: AnalysisReport (domain VO)
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    # 민감 정보 제거 (API 키 등 없지만 방어적)
    safe_dict = {k: v for k, v in result_dict.items() if k != "api_key"}
    result_json = json.dumps(safe_dict, ensure_ascii=False, indent=2)

    prompt = _REPORT_TEMPLATE.format(result_json=result_json)

    loop = asyncio.get_event_loop()
    message = await loop.run_in_executor(
        None,
        partial(
            client.messages.create,
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        ),
    )

    raw = message.content[0].text
    parsed = _parse_json(raw)

    if not parsed:
        logger.warning("[report] JSON 파싱 실패 — 기본 리포트 생성")
        return AnalysisReport(
            title="거시경제 분석 리포트",
            summary=result_dict.get("consensus_rationale", "분석 완료"),
            sections=(
                ReportSection(title="원본 출력", content=raw[:2000], order=0),
            ),
        )

    sections = tuple(
        ReportSection(
            title=s.get("title", f"섹션 {i+1}"),
            content=s.get("content", ""),
            order=i,
        )
        for i, s in enumerate(parsed.get("sections", []))
    )

    report = AnalysisReport(
        title=parsed.get("title", "거시경제 분석 리포트"),
        summary=parsed.get("summary", ""),
        sections=sections,
    )

    logger.info(f"[report] 리포트 생성 완료: {report.title} ({len(sections)}개 섹션)")
    return report


def _parse_json(text: str) -> dict:
    # Claude가 ```json ... ``` 코드블록으로 감쌀 수 있으므로 strip
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = _JSON_PATTERN.search(text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return {}
        return {}
