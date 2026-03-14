"""
Role-profile helpers for portfolio and self-intro packaging.

The core product stays the same. This layer only changes how the same
memo artifact should be explained to different job families.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class RoleProfile:
    name: str
    audience: str
    candidate_positioning: str
    project_translation: str
    primary_value: str
    resume_focus: tuple[str, ...]
    interview_focus: tuple[str, ...]
    emphasis_sections: tuple[str, ...]
    anti_pitch: tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


_FINANCE_AI_IT = RoleProfile(
    name="finance-ai-it",
    audience="은행·증권 AI/데이터·디지털 직무",
    candidate_positioning=(
        "금융 도메인을 이해하고, 정책·금리 신호를 검증 가능한 내부 메모와 "
        "AI 워크플로로 바꾸는 사람"
    ),
    project_translation=(
        "정책/금리 이벤트를 기대분포, 근거, 승인 상태까지 포함한 내부 코파일럿 "
        "산출물로 바꾸는 금융형 AI 시스템"
    ),
    primary_value="내부 업무 자동화, 연구 생산성, 통제 가능한 결과물",
    resume_focus=(
        "RAG/agent보다 evidence와 guardrail을 우선한 설계",
        "정책·금리 해석을 memo artifact로 표준화",
        "profile, schema, tests로 실행 경계를 고정",
    ),
    interview_focus=(
        "왜 투자 추천기 대신 내부 메모 코파일럿으로 좁혔는가",
        "금융기관에서 approval, failsafe, audit를 어떻게 다뤘는가",
        "paper_v2의 calibration 문제를 시스템 기능으로 어떻게 옮겼는가",
    ),
    emphasis_sections=("policy_view", "recommendation", "evidence"),
    anti_pitch=("자동매매", "범용 챗봇", "화려한 멀티에이전트 데모"),
)

_ENTERPRISE_STRATEGY_IT = RoleProfile(
    name="enterprise-strategy-it",
    audience="대기업 IT·전략·재무·IR 인접 직무",
    candidate_positioning=(
        "거시·금리 변화를 사업 환경과 의사결정 맥락으로 번역하는 "
        "business-facing AI/데이터 빌더"
    ),
    project_translation=(
        "정책·금리 변화가 자금조달, 투자, IR, 전략 판단에 어떤 의미를 가지는지 "
        "정리하는 내부 메모 시스템"
    ),
    primary_value="경영 판단 보조, 외부 환경 해석, 실무형 데이터 도구",
    resume_focus=(
        "거시 이벤트를 경영/전략 질문으로 다시 번역한 구조",
        "불확실성 자체를 메시지에 포함한 의사결정 보조 설계",
        "한 프로젝트를 여러 business context로 재사용할 수 있는 packaging",
    ),
    interview_focus=(
        "정책 변화가 사업 의사결정에 미치는 영향 해석",
        "기술 데모가 아니라 실제 내부 사용자 관점으로 설계한 이유",
        "금융 메모 구조를 재무/전략/IR 문맥에 어떻게 전환할 수 있는가",
    ),
    emphasis_sections=("macro_context", "market_context", "policy_view"),
    anti_pitch=("트레이딩 엔진", "고빈도 전략", "크립토 데모"),
)

_BUSINESS_RISK_SALES = RoleProfile(
    name="business-risk-sales",
    audience="캐피탈·영업·리스크·재무/경영관리 직무",
    candidate_positioning=(
        "시장 변화와 금리 환경을 고객·거래처·손익 관점의 메모로 바꿀 수 있는 "
        "데이터 기반 실무형 인재"
    ),
    project_translation=(
        "정책/금리 변화가 시장 대응, 거래처 리스크, 손익 계획에 어떤 함의를 가지는지 "
        "빠르게 정리하는 내부 보조 도구"
    ),
    primary_value="시장 대응, 리스크 헷지, 성과관리 보조",
    resume_focus=(
        "시장 신호를 영업/리스크 언어로 번역한 경험",
        "복잡한 경제 정보를 현업 메모로 축약한 구조",
        "근거와 handoff를 남겨 실무 재사용성을 높인 방식",
    ),
    interview_focus=(
        "정책 변화가 고객/거래처 판단에 주는 영향",
        "결과를 현업이 바로 읽을 수 있게 단순화한 기준",
        "AI보다 시장 해석과 실행가능한 메모를 우선한 이유",
    ),
    emphasis_sections=("macro_context", "recommendation", "evidence"),
    anti_pitch=("모델 성능 자랑", "복잡한 AI 스택 설명", "투자 수익률 중심 설명"),
)

_SECURITIES_TRADING = RoleProfile(
    name="securities-trading",
    audience="증권사 Trading desk",
    candidate_positioning=(
        "데이터분석 자체를 앞세우기보다, 금리와 채권 시장 이벤트를 해석하고 "
        "그 판단 근거를 통계와 데이터로 검증해 desk가 읽을 수 있는 FICC 메모로 구조화하는 사람"
    ),
    project_translation=(
        "미국 금리 경로, 국내 금리커브, 유동성·실행 리스크를 함께 정리해 "
        "rates/FICC desk의 판단 품질을 높이는 내부 메모 코파일럿"
    ),
    primary_value="금리/채권 해석, 커브 시나리오 정리, 실행/유동성 리스크 인식",
    resume_focus=(
        "forecast의 확률/과신 검증을 채권/FICC 문맥으로 번역한 구조",
        "EIMAS를 얇은 rates memo 산출물로 리팩터링한 제품 감각",
        "금리 리스크와 handoff를 같이 남기는 리스크 중심 설계",
    ),
    interview_focus=(
        "왜 데이터분석보다 금리/채권 해석을 앞세우는가",
        "미국 금리 변화와 국내 금리커브를 어떻게 연결해 보는가",
        "자동매매가 아니라 rates/FICC memo로 좁힌 이유는 무엇인가",
    ),
    emphasis_sections=("market_context", "desk_view", "execution_risk", "evidence"),
    anti_pitch=("수익률 자랑", "자동매매", "크립토 과시", "IT 개발자 자기소개", "데이터분석가 자기소개"),
)


_ROLE_PROFILE_ALIASES = {
    "finance-ai-it": "finance-ai-it",
    "finance_ai_it": "finance-ai-it",
    "bank-ai": "finance-ai-it",
    "securities-ai": "finance-ai-it",
    "enterprise-strategy-it": "enterprise-strategy-it",
    "enterprise_strategy_it": "enterprise-strategy-it",
    "strategy-it": "enterprise-strategy-it",
    "corp-strategy": "enterprise-strategy-it",
    "business-risk-sales": "business-risk-sales",
    "business_risk_sales": "business-risk-sales",
    "risk-sales": "business-risk-sales",
    "capital-sales": "business-risk-sales",
    "securities-trading": "securities-trading",
    "securities_trading": "securities-trading",
    "trading": "securities-trading",
    "nh-trading": "securities-trading",
}


_ROLE_PROFILES = {
    "finance-ai-it": _FINANCE_AI_IT,
    "enterprise-strategy-it": _ENTERPRISE_STRATEGY_IT,
    "business-risk-sales": _BUSINESS_RISK_SALES,
    "securities-trading": _SECURITIES_TRADING,
}


def role_profile_choices() -> tuple[str, ...]:
    return tuple(_ROLE_PROFILES.keys())


def resolve_role_profile(name: str | None) -> RoleProfile:
    raw = (name or "finance-ai-it").strip().lower()
    canonical = _ROLE_PROFILE_ALIASES.get(raw)
    if canonical is None:
        supported = ", ".join(role_profile_choices())
        raise ValueError(f"Unsupported role profile '{name}'. Supported: {supported}")
    return _ROLE_PROFILES[canonical]


def build_role_profile_brief(memo: Dict[str, Any], role_profile: RoleProfile) -> Dict[str, Any]:
    recommendation = memo.get("recommendation", {}) if isinstance(memo, dict) else {}
    evidence = memo.get("evidence", {}) if isinstance(memo, dict) else {}

    summary_message = recommendation.get("summary_message", "")
    if not summary_message:
        summary_message = role_profile.project_translation

    handoff_required = bool(recommendation.get("handoff_required", False))
    approval_status = evidence.get("approval_status", {})
    approval_state = "unknown"
    if isinstance(approval_status, dict) and approval_status:
        approval_state = str(approval_status.get("status", "unknown"))

    return {
        "name": role_profile.name,
        "audience": role_profile.audience,
        "candidate_positioning": role_profile.candidate_positioning,
        "project_translation": role_profile.project_translation,
        "primary_value": role_profile.primary_value,
        "resume_focus": list(role_profile.resume_focus),
        "interview_focus": list(role_profile.interview_focus),
        "emphasis_sections": list(role_profile.emphasis_sections),
        "anti_pitch": list(role_profile.anti_pitch),
        "memo_hook": summary_message,
        "control_story": {
            "handoff_required": handoff_required,
            "approval_state": approval_state,
        },
    }


def build_default_role_profile_briefs(memo: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        profile.name: build_role_profile_brief(memo, profile)
        for profile in _ROLE_PROFILES.values()
    }
