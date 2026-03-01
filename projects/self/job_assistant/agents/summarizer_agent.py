"""
SummarizerAgent — 멀티모델 요약

모델 분담:
  OpenAI gpt-4o-mini : JD, COMPANY — 긴 원문 압축 (빠르고 저렴)
  Gemini 2.0 Flash   : SUCCESS — 합격수기 패턴 추출 (구조화 강점)
  Claude Haiku       : INSIDER — 현직자 인터뷰 정리 (맥락 이해)
  Claude Sonnet      : PROFILE — 지원자 fit 매핑 (추론 필요)

모델 키가 없으면 Claude Haiku로 폴백.
"""
import json
import httpx
import anthropic
from typing import List

from agents.base_agent import BaseAgent
from config import API_CONFIG, MODELS
from core.message_bus import JobContext, MessageType
from core.models import CollectedContent, SummarizedSource


# 카테고리 → 담당 모델
CATEGORY_MODEL_MAP = {
    "JD":      "openai",
    "COMPANY": "openai",
    "SUCCESS": "gemini",
    "INSIDER": "anthropic_fast",
}

# 카테고리별 요약 지시
CATEGORY_PROMPTS = {
    "JD": (
        "다음은 채용공고 검색 결과입니다. "
        "직무 내용, 필수 자격요건, 우대사항, 기술 스택을 구조화해 정리하세요. "
        "중복 제거 후 핵심만 남기세요."
    ),
    "COMPANY": (
        "다음은 회사 정보 검색 결과입니다. "
        "회사 비전, 인재상, 최근 사업 방향, 조직문화를 정리하세요. "
        "자소서 작성에 활용할 수 있는 구체적 키워드를 포함하세요."
    ),
    "INSIDER": (
        "다음은 현직자 인터뷰 및 팀 문화 정보입니다. "
        "실제 업무 내용, 하루 일과, 팀 분위기, 성장 기회를 정리하세요. "
        "지원자가 자소서에서 활용할 수 있는 인사이트를 도출하세요."
    ),
    "SUCCESS": (
        "다음은 합격 후기 및 면접 관련 정보입니다. "
        "합격자 공통 스펙, 자소서 핵심 키워드, 면접 자주 출제 질문, "
        "합격 팁을 항목별로 정리하세요."
    ),
}

# NotebookLM 소스 제목 템플릿
NOTEBOOK_TITLES = {
    "JD":      "{company} {role} — 채용공고 및 직무기술서",
    "COMPANY": "{company} — 회사 비전·인재상·사업 방향",
    "INSIDER": "{company} {role} — 현직자 인터뷰·팀 문화",
    "SUCCESS": "{company} {role} — 합격수기·면접 후기",
    "PROFILE": "{company} {role} — 지원자 역량 매핑",
}


class SummarizerAgent(BaseAgent):
    """카테고리별 최적 모델로 요약 → SummarizedSource 목록 생성"""

    def __init__(self):
        super().__init__("SummarizerAgent")

    def _setup_client(self):
        self.anthropic = anthropic.Anthropic(api_key=API_CONFIG.anthropic_key)

    def run(self, context: JobContext) -> List[SummarizedSource]:
        self.log_progress(f"요약 시작: {context.company} / {context.role}")

        collected: CollectedContent = context.collected_content
        if not collected:
            raise ValueError("CollectedContent 없음. CollectorAgent를 먼저 실행하세요.")

        sources: List[SummarizedSource] = []

        for category, raw_text in collected.raw.items():
            if not raw_text.strip():
                self.log_progress(f"  건너뜀 (빈 콘텐츠): {category}")
                continue

            model_key = CATEGORY_MODEL_MAP.get(category, "anthropic_fast")
            prompt = CATEGORY_PROMPTS.get(category, "다음 내용을 핵심 위주로 요약하세요.")
            title = NOTEBOOK_TITLES.get(category, f"{context.company} — {category}").format(
                company=context.company, role=context.role
            )

            self.log_progress(f"  요약 중: {category} (모델: {model_key})")
            try:
                summarized = self._summarize(raw_text, prompt, model_key)
                sources.append(SummarizedSource(
                    title=title,
                    content=summarized,
                    category=category,
                    model_used=model_key,
                ))
            except Exception as e:
                self.log_error(f"요약 실패 ({category}/{model_key}): {e} — Claude로 폴백")
                context.errors.append(f"SummarizerAgent/{category}: {e}")
                try:
                    summarized = self._summarize_claude(raw_text, prompt, fast=True)
                    sources.append(SummarizedSource(
                        title=title,
                        content=summarized,
                        category=category,
                        model_used="anthropic_fast(fallback)",
                    ))
                except Exception as e2:
                    self.log_error(f"폴백도 실패 ({category}): {e2}")

        # PROFILE 소스: 지원자 역량 × 직무 매핑 (Claude Sonnet)
        profile_source = self._build_profile_source(context)
        if profile_source:
            sources.append(profile_source)

        context.summarized_sources = sources

        context.add_message(
            sender="SummarizerAgent",
            receiver="NotebookPublisher",
            content={"source_count": len(sources)},
            msg_type=MessageType.RESULT,
        )

        self.log_success(f"요약 완료: {len(sources)}개 소스 생성")
        return sources

    def _summarize(self, text: str, prompt: str, model_key: str) -> str:
        """모델 키에 따라 적절한 API 호출"""
        if model_key == "openai" and API_CONFIG.openai_key:
            return self._summarize_openai(text, prompt)
        if model_key == "gemini" and API_CONFIG.gemini_key:
            return self._summarize_gemini(text, prompt)
        # 폴백: Claude
        fast = model_key == "anthropic_fast"
        return self._summarize_claude(text, prompt, fast=fast)

    def _summarize_claude(self, text: str, prompt: str, fast: bool = False) -> str:
        model = MODELS["anthropic_fast"] if fast else MODELS["anthropic"]
        msg = self.anthropic.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": f"{prompt}\n\n---\n{text[:8000]}\n---",
            }],
        )
        return msg.content[0].text.strip()

    def _summarize_openai(self, text: str, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {API_CONFIG.openai_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODELS["openai"],
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text[:8000]},
            ],
            "temperature": 0.2,
            "max_tokens": 2048,
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()

    def _summarize_gemini(self, text: str, prompt: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{MODELS['gemini']}:generateContent"
            f"?key={API_CONFIG.gemini_key}"
        )
        payload = {
            "contents": [{
                "parts": [{"text": f"{prompt}\n\n---\n{text[:8000]}\n---"}]
            }],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048},
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

    def _build_profile_source(self, context: JobContext) -> SummarizedSource | None:
        """지원자 역량 × 직무 매핑 소스 생성 (Claude Sonnet)"""
        # source_bank.md 로드
        import os
        source_bank_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "cover_letters", "source_bank.md"
        )
        try:
            with open(source_bank_path, encoding="utf-8") as f:
                source_bank = f.read()
        except FileNotFoundError:
            self.log_error("source_bank.md 없음 — PROFILE 소스 건너뜀")
            return None

        jd_summary = context.summarized_sources[0].content if (
            hasattr(context, "summarized_sources") and context.summarized_sources
        ) else context.collected_content.raw.get("JD", "")

        prompt = f"""다음은 지원자의 보유 경험(source_bank)과 채용공고(JD)입니다.
지원자 경험 중 이 직무에 직결되는 항목을 선별하고,
각 경험이 JD의 어떤 요구사항과 매핑되는지 구체적으로 분석하세요.
"할 수 있다" 관점으로 서술하고, 부족한 부분도 솔직히 진단하세요.

=== 지원자 경험 ===
{source_bank[:4000]}

=== 채용공고 ===
{jd_summary[:2000]}
"""
        title = NOTEBOOK_TITLES["PROFILE"].format(
            company=context.company, role=context.role
        )
        try:
            content = self._summarize_claude(prompt, "", fast=False)
            return SummarizedSource(
                title=title,
                content=content,
                category="PROFILE",
                model_used="anthropic",
            )
        except Exception as e:
            self.log_error(f"PROFILE 소스 생성 실패: {e}")
            return None
