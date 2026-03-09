"""
eco_system GuardrailAgent
메인 에이전트들의 합의 결과를 검증:
- 신호 일관성 체크 (에이전트 간 충돌 감지)
- 데이터 기반 사실 확인 (수집 데이터와 신호 방향 일치 여부)
- 신뢰도 과신 경고 (단일 에이전트 high confidence 시 플래그)
"""

import json
import anthropic
from agents.base import BaseAgent
from core.schemas import AgentRequest, AgentResponse, AgentRole, Signal, EcoResult
from core.config import config


class GuardrailAgent(BaseAgent):
    def __init__(self):
        super().__init__("guardrail", AgentRole.GUARDRAIL)
        self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """요청의 context에 합의 결과가 포함된다고 가정."""
        message = self._client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": request.context}],
        )
        content = message.content[0].text
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", content, re.DOTALL)
            parsed = json.loads(match.group()) if match else {}

        return AgentResponse(
            agent=self.name,
            signal=Signal(parsed.get("signal", "NEUTRAL")),
            confidence=float(parsed.get("confidence", 0.5)),
            rationale=parsed.get("notes", content[:300]),
        )

    @classmethod
    def validate(
        cls,
        result: EcoResult,
        market_data: dict,
        client: anthropic.Anthropic,
    ) -> str:
        """
        합의 결과를 검증하고 guardrail_notes 문자열 반환.
        Orchestrator가 직접 호출하는 클래스 메서드.
        """
        # 에이전트 간 충돌 감지
        signals = [r.signal for r in result.agent_responses]
        conflict = len(set(signals)) > 1 and len(signals) > 1

        # 주요 지표 요약
        vix = market_data.get("vixcls_current") or market_data.get("vix_current", 0)
        spx_ret = market_data.get("gspc_return_30d") or market_data.get("spx_return_30d", 0)
        hy_spread = market_data.get("bamlh0a0hym2", 0)
        yield_curve = market_data.get("t10y2y", 0)

        data_summary = (
            f"VIX={vix:.1f}, SPX 30d={spx_ret:.1f}%, "
            f"HY스프레드={hy_spread:.2f}%, 장단기스프레드={yield_curve:.2f}%"
            if any([vix, spx_ret, hy_spread, yield_curve])
            else "시장 데이터 제한적"
        )

        prompt = (
            f"다음 에이전트 합의 결과를 간략히 검증해줘.\n\n"
            f"합의 신호: {result.consensus_signal.value} ({result.consensus_confidence:.0%})\n"
            f"에이전트 신호: {[r.signal.value for r in result.agent_responses]}\n"
            f"합의 근거: {result.summary}\n"
            f"시장 데이터: {data_summary}\n"
            f"에이전트 충돌 여부: {'있음' if conflict else '없음'}\n\n"
            "체크 항목:\n"
            "1. 신호 방향이 시장 데이터와 논리적으로 일치하는가?\n"
            "2. 에이전트 간 충돌이 있다면 어느 쪽이 더 신뢰할 만한가?\n"
            "3. 신뢰도가 과도하게 높거나 낮은가?\n\n"
            "2~3문장으로 간결하게 검증 메모 작성. "
            "문제 없으면 '합의 결과 정상'으로 시작."
        )

        msg = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
