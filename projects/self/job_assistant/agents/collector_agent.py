"""
CollectorAgent — 멀티카테고리 수집 (Perplexity 기반)

4가지 카테고리를 병렬로 수집:
  JD       : 채용공고 전문, 자격요건, 우대사항
  COMPANY  : 회사 비전, 인재상, 최근 사업 방향
  INSIDER  : 현직자 인터뷰, 블라인드, 팀 문화
  SUCCESS  : 합격수기, 면접 후기, 합격 스펙
"""
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from agents.base_agent import BaseAgent
from config import API_CONFIG, MODELS
from core.message_bus import JobContext, MessageType
from core.models import CollectedContent


# 카테고리별 쿼리 템플릿
# 각 카테고리에 쿼리가 여러 개 → 결과를 합쳐서 raw[category]에 저장
QUERY_TEMPLATES: Dict[str, List[str]] = {
    "JD": [
        "{company} {role} 채용공고 자격요건 우대사항 직무기술서 2025 2026",
        "{company} {role} JD 업무내용 담당업무 하는일",
    ],
    "COMPANY": [
        "{company} 회사 비전 미션 인재상 핵심가치 조직문화 2025 2026",
        "{company} 최근 사업 전략 방향 뉴스 성과 2025 2026",
    ],
    "INSIDER": [
        "{company} {role} 현직자 인터뷰 실제 업무 하루 일과 day-to-day",
        "{company} {role} 블라인드 팀문화 워라밸 업무강도 분위기",
        "{company} {role} 현업 유튜브 링크드인 인터뷰",
    ],
    "SUCCESS": [
        "{company} {role} 합격 후기 자소서 면접 질문 취준 커뮤니티",
        "{company} 인턴 합격 스펙 자소서 팁 면접 준비 2025 2026",
        "{company} {role} 서류 합격 면접 후기 블로그",
    ],
}


class CollectorAgent(BaseAgent):
    """Perplexity로 4카테고리 멀티쿼리 수집"""

    BASE_URL = "https://api.perplexity.ai"
    MAX_WORKERS = 4  # 카테고리 병렬 처리

    def __init__(self):
        super().__init__("CollectorAgent")

    def _setup_client(self):
        self.api_key = API_CONFIG.perplexity_key
        if not self.api_key:
            self.logger.warning("PERPLEXITY_API_KEY 없음")

    def run(self, context: JobContext) -> CollectedContent:
        self.log_progress(f"수집 시작: {context.company} / {context.role}")

        collected = CollectedContent(
            company=context.company,
            role=context.role,
        )

        # 카테고리별 병렬 수집
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = {
                executor.submit(
                    self._collect_category, category, templates, context
                ): category
                for category, templates in QUERY_TEMPLATES.items()
            }

            for future in as_completed(futures):
                category = futures[future]
                try:
                    result = future.result()
                    collected.raw[category] = result
                    collected.sources_used.append(f"perplexity/{category}")
                    self.log_progress(f"  수집 완료: {category} ({len(result)}자)")
                except Exception as e:
                    self.log_error(f"카테고리 실패 ({category}): {e}")
                    context.errors.append(f"CollectorAgent/{category}: {e}")
                    collected.raw[category] = ""

        context.collected_content = collected

        context.add_message(
            sender="CollectorAgent",
            receiver="SummarizerAgent",
            content={"categories": list(collected.raw.keys())},
            msg_type=MessageType.RESULT,
        )

        self.log_success(
            f"수집 완료: {len(collected.raw)}카테고리 "
            f"총 {sum(len(v) for v in collected.raw.values())}자"
        )
        return collected

    def _collect_category(
        self, category: str, templates: List[str], context: JobContext
    ) -> str:
        """카테고리 내 여러 쿼리 실행 후 합치기"""
        parts = []
        for template in templates:
            query = template.format(
                company=context.company,
                role=context.role,
            )
            try:
                result = self._call_perplexity(query)
                parts.append(result)
            except Exception as e:
                self.log_error(f"쿼리 실패 ({category}): {e}")

        return "\n\n---\n\n".join(parts)

    def _call_perplexity(self, query: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODELS["perplexity"],
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "한국 기업 채용 정보 리서처입니다. "
                        "채용공고, 현직자 인터뷰, 합격수기를 정확히 요약하세요. "
                        "출처가 있으면 함께 명시하세요."
                    ),
                },
                {"role": "user", "content": query},
            ],
            "temperature": 0.2,
            "return_citations": True,
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
