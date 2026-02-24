"""
WriterAgent — 자소서 항목별 소스 배분 + gap task 파일 생성
"""
import json
import os
import uuid
from datetime import datetime

import anthropic

from agents.base_agent import BaseAgent
from config import API_CONFIG, MODELS, TASKS_PENDING_DIR, OUTPUTS_DIR
from core.message_bus import JobContext, MessageType
from core.models import Analysis, CoverLetterResult, CoverLetterSection


SYSTEM_PROMPT = """당신은 자소서 전략가입니다.
채용공고 분석 결과와 지원자의 기존 자소서를 바탕으로,
각 자소서 항목에 대해 어떤 경험을 어떻게 배분할지 전략을 세우세요.

반드시 아래 JSON 배열을 출력하세요 (항목 수는 sections 리스트와 동일):
[
  {
    "title": "항목명",
    "source": "기존 자소서에서 재사용할 핵심 내용 (있다면 원문 인용, 없으면 빈 문자열)",
    "tailored": "이 기업/역할에 맞게 조정하는 방향과 포인트 (구체적)",
    "gap": "부족한 부분 또는 추가로 작성해야 할 내용 (없으면 빈 문자열)"
  },
  ...
]

JSON 배열만 출력하고, 다른 텍스트는 포함하지 마세요."""


class WriterAgent(BaseAgent):
    """기존 자소서 + 분석 결과 → 항목별 소스 배분, gap task 저장"""

    def __init__(self):
        super().__init__("WriterAgent")

    def _setup_client(self):
        self.client = anthropic.Anthropic(api_key=API_CONFIG.anthropic_key)

    def run(self, context: JobContext) -> CoverLetterResult:
        self.log_progress(f"자소서 매핑 시작: {context.company} / {context.role}")

        analysis = context.analysis
        if not analysis:
            raise ValueError("Analysis가 없습니다. AnalyzerAgent를 먼저 실행하세요.")

        if not context.cover_letters_raw:
            self.log_error("자소서 파일이 없습니다. data/cover_letters/ 에 .md 또는 .txt 파일을 추가하세요.")
            cover_letters_text = "(자소서 없음)"
            cl_files = []
        else:
            cover_letters_text = self._format_cover_letters(context.cover_letters_raw)
            cl_files = list(context.cover_letters_raw.keys())

        sections_data = self._map_sections(analysis, cover_letters_text)
        sections = []

        os.makedirs(TASKS_PENDING_DIR, exist_ok=True)

        for item in sections_data:
            task_file = None
            if item.get("gap"):
                task_file = self._save_task(context, analysis, item)

            sections.append(
                CoverLetterSection(
                    title=item.get("title", ""),
                    source=item.get("source", ""),
                    tailored=item.get("tailored", ""),
                    gap=item.get("gap", ""),
                    task_file=task_file,
                )
            )

        result = CoverLetterResult(
            company=context.company,
            role=context.role,
            sections=sections,
            cover_letters_used=cl_files,
        )

        context.add_message(
            sender="WriterAgent",
            receiver="USER",
            content={"sections": len(sections), "gaps": len(result.pending_tasks())},
            msg_type=MessageType.RESULT,
        )

        self.log_success(
            f"매핑 완료: {len(sections)}개 항목, "
            f"gap {len(result.pending_tasks())}개 → tasks/pending/"
        )
        return result

    def _format_cover_letters(self, cover_letters_raw: dict) -> str:
        parts = []
        for filename, content in cover_letters_raw.items():
            parts.append(f"=== {filename} ===\n{content}")
        return "\n\n".join(parts)

    def _map_sections(self, analysis: Analysis, cover_letters_text: str) -> list:
        posting = analysis.posting
        user_prompt = f"""
## 채용공고 분석 결과
- 회사: {posting.company}
- 직무: {posting.role}
- 비전: {posting.vision}
- 직무기술: {posting.jd[:1000]}
- 필수 자격요건: {', '.join(posting.requirements)}
- 우대사항: {', '.join(posting.preferred)}
- 현업 업무: {posting.recent_work}
- 핵심 역량: {', '.join(analysis.key_competencies)}
- 강조 키워드: {', '.join(analysis.keywords)}
- 조직문화: {analysis.culture_fit}

## 자소서 항목 목록
{chr(10).join(f'- {s}' for s in analysis.cover_letter_sections)}

## 기존 자소서 내용
{cover_letters_text[:6000]}

위 정보를 바탕으로 각 자소서 항목에 대한 소스 배분 전략을 JSON으로 작성하세요.
"""
        message = self.client.messages.create(
            model=MODELS["anthropic"],
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_output = message.content[0].text.strip()
        if raw_output.startswith("```"):
            lines = raw_output.split("\n")
            raw_output = "\n".join(lines[1:-1])

        try:
            return json.loads(raw_output)
        except json.JSONDecodeError as e:
            self.log_error(f"JSON 파싱 실패: {e}")
            return []

    def _save_task(self, context: JobContext, analysis: Analysis, section: dict) -> str:
        """gap이 있는 항목을 tasks/pending/에 JSON task 파일로 저장"""
        task_id = str(uuid.uuid4())[:8]
        filename = f"task_{context.company}_{section['title']}_{task_id}.json"
        filepath = os.path.join(TASKS_PENDING_DIR, filename)

        task = {
            "task_id": task_id,
            "created_at": datetime.now().isoformat(),
            "company": context.company,
            "role": context.role,
            "section_title": section["title"],
            "gap": section["gap"],
            "tailored_direction": section.get("tailored", ""),
            "keywords": analysis.keywords,
            "key_competencies": analysis.key_competencies,
            "instruction": (
                f"'{context.company}'의 '{context.role}' 포지션 자소서 중 "
                f"'{section['title']}' 항목을 작성하세요.\n\n"
                f"[부족한 부분]\n{section['gap']}\n\n"
                f"[작성 방향]\n{section.get('tailored', '')}\n\n"
                f"[강조 키워드]\n{', '.join(analysis.keywords)}"
            ),
            "output_path": os.path.join(
                OUTPUTS_DIR, f"{context.company}_{section['title']}_{task_id}.md"
            ),
            "status": "pending",
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(task, f, indent=2, ensure_ascii=False)

        self.log_progress(f"  task 저장: {filename}")
        return filepath
