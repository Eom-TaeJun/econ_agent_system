# Agent Teams Architecture - 2026 Edition

## 개념 정리

### ❌ 이것은 Agent Teams가 아닙니다
```bash
# 사람이 수동으로 전환하며 사용
터미널1: claude code
터미널2: codex

개발자 → AI 도구1
개발자 → AI 도구2
```
→ **개발자 생산성 도구** (워크플로우 최적화)

### ✅ 진짜 Agent Teams
```python
# 자동화된 멀티에이전트 시스템
Orchestrator
    ├─> Claude Agent (분석)
    ├─> Gemini Agent (데이터 수집)
    ├─> Perplexity Agent (리서치)
    ├─> Codex Agent (코드 생성)
    └─> 메시지 버스로 자동 통신
```
→ **자율 에이전트 시스템** (자동화된 협업)

## 당신의 현재 시스템 (이미 Agent Teams!)

### 파일 구조
```
econ_agent_system/
├── core/
│   ├── message_bus.py          # ✅ 에이전트 간 통신
│   ├── base_agent.py           # ✅ 에이전트 추상 클래스
│   └── config.py               # ✅ API 설정
├── agents/
│   ├── openai_orchestrator.py  # ✅ 조율자
│   ├── claude_agent.py         # ✅ Claude API
│   ├── gemini_agent.py         # ✅ Gemini API
│   ├── perplexity_agent.py     # ✅ Perplexity API
│   └── codex_agent.py          # ✨ 방금 추가!
└── workflows/
    └── economics_workflow.py   # ✅ 워크플로우
```

### 통신 구조
```python
# message_bus.py에서
class MessageBus:
    def send(self, message: Message):
        """에이전트 간 메시지 전송"""
        self.queues[message.receiver].put(message)
        self.history.append(message)

# 실제 사용 예시
orchestrator.send_message(
    receiver=AgentRole.SEARCHER,  # Perplexity
    content={"query": "Latest Fed policy"},
    msg_type=MessageType.TASK
)

# Perplexity가 자동으로 받아서 처리
# → 결과를 다시 orchestrator에게 전송
```

## 2026년 Agent Teams 구성 방법

### 방법 1: 기존 시스템 확장 (추천!)
```python
# 당신의 시스템에 새 에이전트 추가
from agents.codex_agent import CodexAgent

# 오케스트레이터에 등록
orchestrator = OpenAIOrchestrator()
orchestrator.register_agent(CodexAgent())
orchestrator.register_agent(ClaudeAgent())
orchestrator.register_agent(GeminiAgent())

# 자동으로 작업 분배
await orchestrator.run_workflow({
    'task': 'Analyze market trends',
    'subtasks': [
        {'type': 'research', 'agent': 'perplexity'},
        {'type': 'code', 'agent': 'codex'},
        {'type': 'analysis', 'agent': 'claude'}
    ]
})
```

### 방법 2: 프레임워크 사용

#### AutoGen (Microsoft)
```python
# 2026년 최신 버전
from autogen import ConversableAgent, GroupChat

claude_agent = ConversableAgent(
    name="Analyst",
    llm_config={"model": "claude-sonnet-4-5"},
    system_message="You analyze market data"
)

codex_agent = ConversableAgent(
    name="Coder",
    llm_config={"model": "gpt-5.3-codex"},
    system_message="You generate code"
)

groupchat = GroupChat(
    agents=[claude_agent, codex_agent],
    messages=[],
    max_round=10
)

groupchat.initiate_chat("Analyze S&P500 and generate viz code")
```

#### LangGraph (LangChain)
```python
from langgraph.graph import StateGraph

# 상태 정의
class AgentState(TypedDict):
    query: str
    research: str
    code: str
    analysis: str

# 에이전트 노드
graph = StateGraph(AgentState)
graph.add_node("research", perplexity_agent)
graph.add_node("code", codex_agent)
graph.add_node("analyze", claude_agent)

# 워크플로우 정의
graph.add_edge("research", "code")
graph.add_edge("code", "analyze")
graph.set_entry_point("research")

app = graph.compile()
result = await app.ainvoke({"query": "Market analysis"})
```

#### CrewAI
```python
from crewai import Agent, Task, Crew

researcher = Agent(
    role='Market Researcher',
    goal='Find latest market trends',
    backstory='Expert in financial research',
    llm='perplexity-online'
)

coder = Agent(
    role='Data Engineer',
    goal='Generate data collection code',
    backstory='Expert in Python and APIs',
    llm='gpt-5.3-codex'
)

analyst = Agent(
    role='Financial Analyst',
    goal='Provide market insights',
    backstory='Senior analyst with 10 years experience',
    llm='claude-sonnet-4-5'
)

crew = Crew(
    agents=[researcher, coder, analyst],
    tasks=[research_task, coding_task, analysis_task],
    process='sequential'  # or 'hierarchical'
)

result = crew.kickoff()
```

### 방법 3: MCP 통합 (Model Context Protocol)

```json
// ~/.claude/mcp_settings.json
{
  "mcpServers": {
    "codex-server": {
      "command": "npx",
      "args": ["@openai/codex-mcp-server"],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

```python
# Claude Code에서 Codex를 도구로 사용
from mcp import MCPClient

client = MCPClient("codex-server")
result = client.call_tool(
    "generate_code",
    prompt="Create a stock price fetcher"
)
```

## 실전 통합 예시

### 당신의 시스템에 Codex Agent 추가

#### 1. Agent 등록
```python
# econ_agent_system/workflows/economics_workflow.py

from agents.codex_agent import CodexAgent

class EconomicsWorkflow:
    def __init__(self):
        self.bus = MESSAGE_BUS
        self.orchestrator = OpenAIOrchestrator()
        self.perplexity = PerplexityAgent()
        self.claude = ClaudeAgent()
        self.gemini = GeminiAgent()
        self.codex = CodexAgent()  # ✨ 추가!

        # 에이전트 역할 정의
        self.agents = {
            'orchestrator': self.orchestrator,
            'searcher': self.perplexity,
            'analyst': self.claude,
            'collector': self.gemini,
            'coder': self.codex  # ✨ 추가!
        }
```

#### 2. 워크플로우 업데이트
```python
async def run_full_analysis(self, query: str):
    """전체 분석 워크플로우"""

    # Phase 1: 리서치 (Perplexity)
    research_task = Message(
        msg_type=MessageType.TASK,
        sender=AgentRole.ORCHESTRATOR,
        receiver=AgentRole.SEARCHER,
        content={"query": query}
    )
    self.bus.send(research_task)

    # Phase 2: 데이터 수집 코드 생성 (Codex) ✨ 새로운 단계!
    code_task = Message(
        msg_type=MessageType.TASK,
        sender=AgentRole.ORCHESTRATOR,
        receiver=AgentRole.CODER,
        content={
            "task": "Generate data collection script",
            "requirements": "Fetch Fed data and market indicators"
        }
    )
    self.bus.send(code_task)

    # Phase 3: 코드 실행 & 데이터 수집 (Gemini)
    # Phase 4: 분석 (Claude)
    # Phase 5: 종합 (Orchestrator)
```

#### 3. 에이전트 간 협업
```python
# 특화 협업 패턴
async def collaborative_code_development(self):
    """Codex + Claude 협업 패턴"""

    # 1. Codex가 초안 생성
    draft = await self.codex.process(
        "Create API client for FRED",
        context
    )

    # 2. Claude가 리뷰 및 개선
    review_task = Message(
        msg_type=MessageType.TASK,
        sender=AgentRole.ORCHESTRATOR,
        receiver=AgentRole.ANALYST,
        content={
            "action": "review_code",
            "code": draft['code'],
            "focus": ["error_handling", "edge_cases", "performance"]
        }
    )
    self.bus.send(review_task)

    # 3. 결과 통합
    reviewed = self.bus.receive(AgentRole.ORCHESTRATOR)
    final_code = reviewed.content['improved_code']

    return final_code
```

## 에이전트 역할 분담 (최적화)

| 에이전트 | 전문 분야 | 사용 시나리오 |
|---------|----------|--------------|
| **OpenAI Orchestrator** | 조율, 계획, 의사결정 | 워크플로우 관리, 작업 분배 |
| **Claude (Sonnet 4.5)** | 분석, 추론, 아키텍처 | 시장 분석, 코드 리뷰, 전략 수립 |
| **Gemini** | 멀티모달, 데이터 처리 | 차트 분석, 대량 데이터 처리 |
| **Perplexity** | 실시간 검색, 리서치 | 최신 뉴스, 시장 동향 조사 |
| **Codex** | 코드 생성, 자동화 | API 클라이언트, 스크립트 생성 |

### 작업 분배 예시

```python
# 복잡한 경제 분석 프로젝트
project = "Analyze impact of Fed rate changes on crypto markets"

workflow = {
    # 1. 리서치 (Perplexity)
    'research': {
        'agent': 'perplexity',
        'tasks': [
            'Find latest Fed announcements',
            'Get crypto market news',
            'Research historical correlations'
        ]
    },

    # 2. 데이터 수집 (Codex → Gemini)
    'data_collection': {
        'code_gen': {
            'agent': 'codex',
            'task': 'Generate FRED + crypto API clients'
        },
        'execution': {
            'agent': 'gemini',
            'task': 'Run scripts and collect data'
        }
    },

    # 3. 분석 (Claude)
    'analysis': {
        'agent': 'claude',
        'tasks': [
            'Critical path analysis',
            'Correlation analysis',
            'Regime detection'
        ]
    },

    # 4. 코드 생성 (Codex)
    'visualization': {
        'agent': 'codex',
        'task': 'Generate matplotlib visualization code'
    },

    # 5. 종합 (Orchestrator + Claude)
    'synthesis': {
        'orchestrator': 'Coordinate findings',
        'claude': 'Write final report'
    }
}
```

## 2026년 2월 이후 새로운 기능

### 1. 에이전트 간 메모리 공유
```python
from crewai.memory import SharedMemory

shared_memory = SharedMemory()

# 모든 에이전트가 공유
researcher.memory = shared_memory
coder.memory = shared_memory
analyst.memory = shared_memory

# 자동으로 컨텍스트 유지
```

### 2. 동적 에이전트 생성
```python
# 작업에 따라 에이전트 자동 생성
orchestrator.create_specialist_agent(
    role="Crypto Expert",
    model="claude-opus-4-6",
    knowledge_base="crypto_markets_2024-2026"
)
```

### 3. 멀티모달 협업
```python
# 이미지, 텍스트, 코드 동시 처리
result = await multi_modal_analysis(
    text_data=market_reports,
    image_data=charts,
    code_data=analysis_scripts
)
```

## 실행 예시

```bash
# 당신의 시스템에서 실행
cd /home/tj/projects/autoai/econ_agent_system/econ_agent_system

# Codex agent 테스트
python -m agents.codex_agent

# 전체 워크플로우 실행
python main.py --query "Analyze Fed rate impact on markets" --agents all
```

## 다음 단계

1. **Codex Agent 통합 테스트**
   ```bash
   cd econ_agent_system/econ_agent_system
   python -m agents.codex_agent
   ```

2. **워크플로우 업데이트**
   - `workflows/economics_workflow.py`에 Codex 추가
   - 코드 생성 단계 추가

3. **협업 패턴 구현**
   - Codex-Claude 코드 리뷰 파이프라인
   - Perplexity-Codex 데이터 수집 자동화

4. **성능 측정**
   - 단일 에이전트 vs 멀티 에이전트 비교
   - 작업 완료 시간, 정확도 측정

## 참고 자료

- **AutoGen**: https://microsoft.github.io/autogen/
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **CrewAI**: https://docs.crewai.com/
- **MCP Protocol**: https://modelcontextprotocol.io/

---

**핵심 요약:**

1. ✅ 당신은 이미 진짜 Agent Teams 시스템을 가지고 있음
2. ✅ Codex를 **에이전트로** 추가하는 것이 올바른 방법
3. ❌ 터미널 2개로 수동 전환하는 것은 Agent Teams가 아님
4. 🎯 다음: 기존 시스템에 Codex Agent를 통합하고 자동화된 협업 구현

**당신의 시스템 = 2026년 최신 Agent Teams 아키텍처 ✨**
