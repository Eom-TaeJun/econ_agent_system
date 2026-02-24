"""
AnalyzerAgent — 검색 결과를 Claude로 구조화 분석
"""
import json
import anthropic

from agents.base_agent import BaseAgent
from config import API_CONFIG, MODELS
from core.message_bus import JobContext, MessageType
from core.models import Analysis, JobPosting


SYSTEM_PROMPT = """당신은 채용공고 분석 전문가입니다.
주어진 채용공고 검색 결과를 분석하여 JSON 형식으로 구조화하세요.

반드시 아래 JSON 스키마를 따르세요:
{
  "vision": "회사 비전/미션 (1-3문장)",
  "jd": "직무기술서 요약",
  "requirements": ["필수 자격요건1", "필수 자격요건2", ...],
  "preferred": ["우대사항1", "우대사항2", ...],
  "recent_work": "현업에서 실제로 하는 일 (구체적)",
  "key_competencies": ["핵심역량1", "핵심역량2", ...],
  "technical_skills": ["기술스킬1", "기술스킬2", ...],
  "soft_skills": ["소프트스킬1", "소프트스킬2", ...],
  "culture_fit": "조직문화 및 인재상 요약",
  "keywords": ["자소서에서 강조해야 할 키워드1", ...],
  "cover_letter_sections": ["지원동기", "직무역량", "성장경험", ...]
}

JSON만 출력하고, 다른 텍스트는 포함하지 마세요."""


class AnalyzerAgent(BaseAgent):
    """Claude로 검색 결과 → 구조화된 분석"""

    def __init__(self):
        super().__init__("AnalyzerAgent")

    def _setup_client(self):
        self.client = anthropic.Anthropic(api_key=API_CONFIG.anthropic_key)

    def run(self, context: JobContext) -> Analysis:
        self.log_progress(f"분석 시작: {context.company} / {context.role}")

        posting = context.job_posting
        if not posting:
            raise ValueError("JobPosting이 없습니다. SearchAgent를 먼저 실행하세요.")

        raw = posting.raw_search or posting.jd
        structured = self._analyze(context.company, context.role, raw)

        # JobPosting 필드 보강
        posting.vision = structured.get("vision", "")
        posting.jd = structured.get("jd", raw)
        posting.requirements = structured.get("requirements", [])
        posting.preferred = structured.get("preferred", [])
        posting.recent_work = structured.get("recent_work", "")

        analysis = Analysis(
            posting=posting,
            key_competencies=structured.get("key_competencies", []),
            technical_skills=structured.get("technical_skills", []),
            soft_skills=structured.get("soft_skills", []),
            culture_fit=structured.get("culture_fit", ""),
            keywords=structured.get("keywords", []),
            cover_letter_sections=structured.get(
                "cover_letter_sections", ["지원동기", "직무역량", "성장경험", "입사 후 포부"]
            ),
        )

        context.analysis = analysis
        context.add_message(
            sender="AnalyzerAgent",
            receiver="WriterAgent",
            content={
                "competencies": analysis.key_competencies,
                "sections": analysis.cover_letter_sections,
            },
            msg_type=MessageType.RESULT,
        )

        self.log_success(
            f"분석 완료: 핵심역량 {len(analysis.key_competencies)}개, "
            f"자소서항목 {len(analysis.cover_letter_sections)}개"
        )
        return analysis

    def _analyze(self, company: str, role: str, raw_search: str) -> dict:
        user_prompt = f"""아래는 '{company}'의 '{role}' 포지션에 대한 검색 결과입니다.
이를 분석하여 JSON을 생성하세요.

--- 검색 결과 ---
{raw_search[:8000]}
--- 끝 ---
"""
        message = self.client.messages.create(
            model=MODELS["anthropic"],
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_output = message.content[0].text.strip()

        # JSON 파싱 (마크다운 코드블록 제거)
        if raw_output.startswith("```"):
            lines = raw_output.split("\n")
            raw_output = "\n".join(lines[1:-1])

        try:
            return json.loads(raw_output)
        except json.JSONDecodeError as e:
            self.log_error(f"JSON 파싱 실패: {e}\n출력: {raw_output[:500]}")
            return {}
