"""
infrastructure/report/writer.py

AnalysisReport → MD/HTML 파일 출력.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from domain.report import AnalysisReport

logger = logging.getLogger(__name__)


def write_report(
    report: AnalysisReport,
    output_dir: str = "outputs",
    fmt: str = "md",
) -> str:
    """
    AnalysisReport를 파일로 저장.

    fmt: "md" 또는 "html"
    Returns: 저장된 파일 경로
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    today = str(date.today())
    filename = f"report_{today}.{fmt}"
    filepath = str(Path(output_dir) / filename)

    if fmt == "html":
        content = _to_html(report)
    else:
        content = report.to_markdown()

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"[report_writer] 저장 완료: {filepath}")
    return filepath


def _to_html(report: AnalysisReport) -> str:
    """AnalysisReport → 간단한 HTML."""
    sections_html = ""
    for section in sorted(report.sections, key=lambda s: s.order):
        # 간단한 마크다운 → HTML 변환 (줄바꿈만)
        content = section.content.replace("\n", "<br>\n")
        sections_html += f"<h2>{section.title}</h2>\n<p>{content}</p>\n"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{report.title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               max-width: 800px; margin: 40px auto; padding: 0 20px;
               color: #333; line-height: 1.6; }}
        h1 {{ color: #1a1a1a; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        h2 {{ color: #2c3e50; margin-top: 30px; }}
        blockquote {{ border-left: 4px solid #3498db; padding-left: 15px;
                     color: #555; font-style: italic; }}
        .meta {{ color: #888; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>{report.title}</h1>
    <blockquote>{report.summary}</blockquote>
    {sections_html}
    <hr>
    <p class="meta">Generated at {report.generated_at} by eco_system_v2</p>
</body>
</html>"""
