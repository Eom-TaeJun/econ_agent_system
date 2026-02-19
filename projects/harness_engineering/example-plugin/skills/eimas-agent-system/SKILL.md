---
name: eimas-agent-system
description: |
  Economic Intelligence Multi-Agent System (EIMAS) 아키텍처.
  멀티에이전트 경제 분석 시스템 설계, MessageBus 기반 에이전트 통신,
  Orchestrator-Worker 패턴, 다중 AI API(Claude/GPT/Gemini/Perplexity) 조합 작업 시 활성화.
version: 1.0.0
updated: 2026-02-20
source: projects/autoai/CLAUDE.md + AGENT_TEAMS_ARCHITECTURE.md
---

# EIMAS 아키텍처 표준

## 에이전트 역할 구조

| 에이전트 | Provider | 역할 |
|---------|---------|------|
| **Orchestrator** | OpenAI GPT-4 | 프로젝트 총괄, 계획, 결과 통합 |
| **Searcher** | Perplexity | 학술 연구, 웹 검색, 데이터 소스 발견 |
| **Coder** | Claude | Python 코드 생성, 데이터 분석, 시각화 |
| **Collector** | Gemini | 경제 데이터 수집, API 호출 |

## 통신 구조 (MessageBus)

```python
# core/message_bus.py
class MessageBus:
    def send(self, message: Message):
        self.queues[message.receiver].put(message)
        self.history.append(message)

# 사용 패턴
orchestrator.send_message(
    receiver=AgentRole.SEARCHER,
    content={"query": "Latest Fed policy stance"},
    msg_type=MessageType.TASK
)
# Perplexity가 자동 처리 → 결과를 orchestrator에게 전송
```

## 디렉토리 구조

```
eimas/
├── core/
│   ├── config.py          # APIConfig (API 키 관리)
│   ├── message_bus.py     # 에이전트 간 통신
│   ├── base_agent.py      # BaseAgent 추상 클래스
│   ├── schemas.py         # 데이터 스키마
│   └── debate.py          # 토론 프로토콜
├── agents/
│   ├── openai_orchestrator.py  # 총괄 (GPT-4)
│   ├── claude_agent.py         # 코딩/분석
│   ├── gemini_agent.py         # 데이터 수집
│   └── perplexity_agent.py     # 검색
├── workflows/
│   └── economics_workflow.py   # 워크플로우 템플릿
└── outputs/                    # 결과 저장
```

## 분석 방법론 (내장)

```
1. 변수 선택: LASSO (L1 정규화)
2. Treasury 제외: Simultaneity 문제 방지
3. Horizon 분리: 초단기/단기/장기
4. Critical Path: Granger Causality 기반 전이 경로
5. 리스크 분해: VIX = Uncertainty + Risk Appetite (Bekaert et al.)
```

## 에이전트 추가 패턴

```python
from core.base_agent import BaseAgent
from core.message_bus import MessageBus

class NewSpecialistAgent(BaseAgent):
    def __init__(self, message_bus: MessageBus):
        super().__init__(AgentRole.SPECIALIST, message_bus)

    async def process_task(self, task: dict) -> dict:
        # 분석 로직
        result = await self.analyze(task["data"])
        return {"status": "complete", "result": result}

# 오케스트레이터에 등록
orchestrator.register_agent(NewSpecialistAgent(bus))
```

## 실행 방법

```bash
# interactive 모드
python main.py

# 직접 쿼리
python main.py --query "Fed 금리 경로 분석" --auto

# 워크플로우 템플릿 사용
python main.py --query "..." --template variable_discovery
```

## 환경 변수 (필수)

```bash
export ANTHROPIC_API_KEY='sk-ant-...'
export OPENAI_API_KEY='sk-...'
export GOOGLE_API_KEY='AI...'
export PERPLEXITY_API_KEY='pplx-...'
export FRED_API_KEY='...'        # 선택
```

## 코딩 컨벤션

- Python 3.10+, Type hints 필수
- 한글 주석 허용, 경제학 용어는 영어 유지
- 결과는 `outputs/` 하위에만 저장
- 각 에이전트는 `BaseAgent` 상속

---
상세 아키텍처: `references/architecture.md`
원본 위치: `projects/autoai/econ_agent_system/`
