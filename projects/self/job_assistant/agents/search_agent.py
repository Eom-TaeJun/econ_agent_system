"""
SearchAgent — Perplexity로 채용공고 검색
"""
import httpx
from typing import Dict

from agents.base_agent import BaseAgent
from config import API_CONFIG, MODELS
from core.message_bus import JobContext, MessageType
from core.models import JobPosting


class SearchAgent(BaseAgent):
    """Perplexity API로 기업 공고·비전·JD·우대사항을 검색"""

    BASE_URL = "https://api.perplexity.ai"

    def __init__(self):
        super().__init__("SearchAgent")

    def _setup_client(self):
        self.api_key = API_CONFIG.perplexity_key
        if not self.api_key:
            self.logger.warning("PERPLEXITY_API_KEY 없음")

    def run(self, context: JobContext) -> JobPosting:
        self.log_progress(f"검색 시작: {context.company} / {context.role}")

        queries = self._build_queries(context)
        combined = []

        for label, query in queries.items():
            self.log_progress(f"  쿼리: {label}")
            try:
                result = self._call_api(query)
                combined.append(f"=== {label} ===\n{result}")
            except Exception as e:
                self.log_error(f"쿼리 실패 ({label}): {e}")
                context.errors.append(f"SearchAgent/{label}: {e}")

        raw = "\n\n".join(combined)
        context.search_result = {"raw": raw}

        posting = self._parse_to_posting(context, raw)
        context.job_posting = posting

        context.add_message(
            sender="SearchAgent",
            receiver="AnalyzerAgent",
            content={"company": posting.company, "role": posting.role},
            msg_type=MessageType.RESULT,
        )

        self.log_success(f"검색 완료: {posting.company} — {posting.role}")
        return posting

    def _build_queries(self, context: JobContext) -> Dict[str, str]:
        company = context.company
        role = context.role

        if context.url:
            return {
                "공고_전문": f"site:{context.url} OR {company} {role} 채용공고 자격요건 우대사항 직무기술서",
                "회사_비전": f"{company} 회사 비전 미션 인재상 조직문화 2024 2025",
                "현업_업무": f"{company} {role} 현직자 실제 업무 하루 일과 인터뷰",
            }

        return {
            "공고_JD": f"{company} {role} 채용공고 자격요건 우대사항 직무기술서 2025",
            "회사_비전": f"{company} 회사 비전 미션 인재상 조직문화 핵심가치",
            "현업_업무": f"{company} {role} 현직자 실제 업무 day-to-day 인터뷰 블로그",
            "기술스택": f"{company} {role} 기술스택 사용언어 프레임워크 데이터 인프라",
        }

    def _call_api(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODELS["perplexity"],
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 채용 정보 리서처입니다. 한국 기업의 채용공고, 직무기술, 조직문화를 정확하게 요약하세요.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "return_citations": True,
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f"{self.BASE_URL}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _parse_to_posting(self, context: JobContext, raw: str) -> JobPosting:
        """검색 결과 텍스트를 JobPosting으로 파싱 (간단 휴리스틱)"""
        # AnalyzerAgent가 정밀 파싱을 담당하므로 여기선 raw를 jd에 담아 전달
        return JobPosting(
            company=context.company,
            role=context.role,
            vision="",           # AnalyzerAgent가 채움
            jd=raw,              # raw 전체를 JD로 임시 보관
            requirements=[],
            preferred=[],
            recent_work="",
            source_url=context.url,
            raw_search=raw,
        )
