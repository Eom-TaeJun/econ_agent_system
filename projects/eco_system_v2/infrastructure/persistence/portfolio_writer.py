"""
infrastructure/persistence/portfolio_writer.py

eco_system_v2 분석 결과 + job_assistant ProfileData를
포트폴리오용 마크다운 리포트로 저장.

출력: outputs/portfolio/{company}_{role}_{date}.md
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def write_portfolio(
    result: dict,
    profile_dict: dict,
    output_dir: str = "outputs/portfolio",
) -> str:
    """
    분석 결과 + 프로필을 마크다운 리포트로 저장.

    result: EcoResult.to_dict() 출력
    profile_dict: ProfileData.to_dict() 출력
    반환: 저장된 파일 경로
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    company = profile_dict.get("company", "unknown")
    role = profile_dict.get("role", "unknown")
    date = result.get("date", "unknown")

    filename = f"{company}_{role}_{date}.md"
    filepath = str(Path(output_dir) / filename)

    md = _render(result, profile_dict)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)

    logger.info(f"[portfolio_writer] 저장 완료: {filepath}")
    return filepath


def _render(result: dict, profile: dict) -> str:
    company = profile.get("company", "")
    role = profile.get("role", "")
    date = result.get("date", "")
    signal = result.get("consensus_signal", "")
    confidence = result.get("consensus_confidence", 0.0)
    rationale = result.get("consensus_rationale", "")

    signal_emoji = {"BULLISH": "▲", "NEUTRAL": "─", "BEARISH": "▼"}.get(signal, "?")

    # 에이전트별 결과 테이블
    agent_rows = ""
    for s in result.get("agent_signals", []):
        agent_rows += (
            f"| {s.get('agent','')} "
            f"| {s.get('signal','')} "
            f"| {s.get('confidence', 0):.0%} "
            f"| {s.get('rationale','')[:80]}... |\n"
        )

    # 시장 데이터 테이블
    md_data = result.get("market_data", {})
    vix_c = md_data.get("vix_current", 0.0)
    vix_a = md_data.get("vix_30d_avg", 0.0)
    spx = md_data.get("spx_return_30d", 0.0)
    fed = md_data.get("fed_rate", 0.0)

    # 역량 목록
    competencies = profile.get("key_competencies", [])
    keywords = profile.get("keywords", [])
    tech_skills = profile.get("technical_skills", [])

    comp_lines = "\n".join(f"- {c}" for c in competencies) if competencies else "- (없음)"
    kw_line = ", ".join(keywords) if keywords else "(없음)"
    tech_line = ", ".join(tech_skills) if tech_skills else "(없음)"

    return f"""# 거시경제 분석 리포트

| 항목 | 내용 |
|------|------|
| **대상 기업** | {company} |
| **지원 직무** | {role} |
| **분석일** | {date} |
| **분석 시스템** | eco_system_v2 (경량 DDD + Hub-and-Spoke) |

---

## 종합 신호: {signal_emoji} {signal} (신뢰도 {confidence:.0%})

> {rationale}

---

## 에이전트별 분석

| 에이전트 | 신호 | 신뢰도 | 근거 요약 |
|---------|------|-------|---------|
{agent_rows.rstrip()}

---

## 시장 데이터 스냅샷

| 지표 | 값 |
|------|----|
| VIX (현재) | {vix_c:.1f} |
| VIX (30일 평균) | {vix_a:.1f} |
| S&P500 30일 수익률 | {spx:+.1f}% |
| 연방기금금리 | {fed:.2f}% |

---

## {company} × {role} 직무 연관성

**이 분석이 해당 직무에서 의미하는 것:**

현재 거시경제 신호({signal})는 {company}의 {role} 직무와 다음과 같이 연결됩니다.

**직무 핵심 역량:**
{comp_lines}

**관련 기술 스킬:** {tech_line}

**자소서 핵심 키워드:** {kw_line}

---

*eco_system_v2로 생성 — 멀티에이전트 거시경제 분석 시스템*
"""
