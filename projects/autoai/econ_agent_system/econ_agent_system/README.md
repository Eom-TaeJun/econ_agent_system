# 🤖 Multi-Agent Economics Analysis System

AI 에이전트 기반의 경제 분석 자동화 시스템입니다. 4개의 AI가 협업하여 경제 데이터 분석 프로젝트를 자동으로 수행합니다.

## 🎯 시스템 개요

| Agent | Provider | Role | 역할 (한국어) |
|-------|----------|------|--------------|
| 🎯 Orchestrator | OpenAI GPT-4 | Project coordination & synthesis | 프로젝트 총괄, 계획 수립, 결과 통합 |
| 📡 Searcher | Perplexity | Research & web search | 학술 연구, 웹 검색, 데이터 소스 발견 |
| 💻 Coder | Claude | Code generation & analysis | Python 코드 생성, 데이터 분석, 시각화 |
| 📊 Collector | Gemini | Data collection | 경제 데이터 수집, API 호출, 데이터 처리 |

## 🚀 Quick Start

### 1. API 키 설정 (WSL/bash)

```bash
# ~/.bashrc 또는 nano로 설정
export OPENAI_API_KEY='sk-...'
export ANTHROPIC_API_KEY='sk-ant-...'
export GEMINI_API_KEY='AI...'
export PERPLEXITY_API_KEY='pplx-...'

# 선택사항: FRED API 키 (데이터 수집용)
export FRED_API_KEY='...'

# 변경사항 적용
source ~/.bashrc
```

### 2. 설치

```bash
cd econ_agent_system
pip install -r requirements.txt
```

### 3. 실행

```bash
# Interactive 모드
python main.py

# 직접 쿼리
python main.py --query "Analyze the relationship between inflation and unemployment"

# Auto 모드 (사용자 개입 없음)
python main.py --query "..." --auto

# 템플릿 사용
python main.py --query "..." --template variable_discovery
```

## 📁 프로젝트 구조

```
econ_agent_system/
├── main.py                 # 메인 진입점
├── requirements.txt        # 의존성
├── core/
│   ├── config.py          # API 설정
│   ├── message_bus.py     # 에이전트 간 통신
│   └── base_agent.py      # 기본 에이전트 클래스
├── agents/
│   ├── openai_orchestrator.py  # 총괄 에이전트 (GPT-4)
│   ├── perplexity_agent.py     # 검색 에이전트
│   ├── claude_agent.py         # 코딩 에이전트
│   └── gemini_agent.py         # 데이터 수집 에이전트
├── workflows/
│   └── economics_workflow.py   # 경제학 워크플로우 템플릿
├── data/                   # 수집된 데이터
├── outputs/                # 결과물 저장
└── logs/                   # 로그 파일
```

## 📋 워크플로우 템플릿

### 1. Variable Discovery (변수 발견)
의미 있는 경제 변수 발견 및 분석

### 2. Correlation Analysis (상관관계 분석)
경제 변수 간 상관관계 분석

### 3. Regression Modeling (회귀 모델링)
회귀 모델 구축 및 검증

### 4. Time Series Analysis (시계열 분석)
경제 시계열 데이터 분석

### 5. Macro Indicator (거시경제 지표)
거시경제 지표 분석 및 대시보드

## 🔄 실행 흐름

```
[User Query]
    ↓
[OpenAI Orchestrator] ← 계획 수립
    ↓
[Perplexity] → Research results → [Context]
    ↓
[Gemini] → Data collection code → [Context]
    ↓
[Claude] → Analysis code + Visualization → [Context]
    ↓
[OpenAI Orchestrator] ← 결과 통합
    ↓
[Final Report]
```

## 🛑 사용자 개입 (Checkpoints)

Auto 모드가 아닌 경우, 주기적으로 체크포인트에서 멈춥니다:

```
⏸️  CHECKPOINT - User Intervention Point
==========================================
Current Phase: Data Collection
Progress: [Context Summary]

Options:
  [c] Continue
  [m] Modify plan
  [s] Skip to next phase
  [q] Quit
==========================================
```

## 📊 예시 쿼리

```python
# 기본 분석
"Analyze the relationship between US GDP growth and stock market returns"

# 변수 발견
"Find meaningful variables that predict inflation in Korea"

# 시계열 분석
"Forecast Korean export growth using leading indicators"

# 상관관계
"What economic variables are most correlated with housing prices?"

# 복합 분석
"Compare the effectiveness of monetary policy in US vs EU using data from 2010-2023"
```

## ⚙️ 설정 옵션

`core/config.py`에서 수정 가능:

```python
AGENT_CONFIG = AgentConfig(
    max_iterations=10,           # 최대 반복 횟수
    checkpoint_frequency=3,      # N 단계마다 체크포인트
    auto_mode=False,             # 자동 모드
    verbose=True,                # 상세 로그
    log_to_file=True,            # 파일 로깅
)
```

## 📝 출력 형식

결과는 `outputs/project_{task_id}.json`에 저장됩니다:

```json
{
  "task_id": "abc123",
  "query": "...",
  "plan": {...},
  "results": {
    "phase_1": {...},
    "phase_2": {...},
    "phase_3": {...}
  },
  "final_output": {
    "synthesis": "...",
    "generated_at": "..."
  }
}
```

## 🔧 확장하기

### 새 에이전트 추가

```python
from core.base_agent import BaseAgent, AgentRegistry

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.CUSTOM, "My-Agent")
    
    def _setup_client(self):
        # API 클라이언트 설정
        pass
    
    async def process(self, task, context):
        # 태스크 처리 로직
        pass

# 등록
AgentRegistry.register(MyAgent())
```

### 새 워크플로우 추가

```python
from workflows.economics_workflow import WorkflowTemplate, WorkflowType

my_template = WorkflowTemplate(
    name="My Analysis",
    workflow_type=WorkflowType.CUSTOM,
    description="...",
    research_queries=[...],
    data_requirements=[...],
    analysis_tasks=[...],
    expected_outputs=[...]
)
```

## ⚠️ 주의사항

1. **API 비용**: 각 API 호출에 비용이 발생합니다. Auto 모드 사용 시 주의하세요.
2. **Rate Limits**: API별 호출 제한을 확인하세요.
3. **데이터 품질**: 자동 수집된 데이터는 검증이 필요합니다.
4. **결과 검토**: AI 생성 코드와 분석은 반드시 검토하세요.

## 📞 문제 해결

### API 키 오류
```bash
# 키 확인
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
```

### 모듈 import 오류
```bash
# 프로젝트 루트에서 실행
cd econ_agent_system
python main.py
```

### 타임아웃 오류
API 호출 타임아웃을 늘리거나 쿼리를 단순화하세요.

---

## 📜 License

MIT License

## 🇰🇷 한국어 요약

이 시스템은 4개의 AI 에이전트가 협업하여 경제 분석 프로젝트를 자동화합니다:
- **OpenAI GPT-4**: 전체 프로젝트 총괄 및 조율
- **Perplexity**: 학술 연구 및 데이터 소스 검색
- **Claude**: Python 코드 생성 및 분석
- **Gemini**: 경제 데이터 수집

사용자가 분석 요청을 입력하면, 에이전트들이 자동으로 계획을 수립하고, 필요한 연구를 수행하며, 데이터를 수집하고, 분석 코드를 생성하여 최종 리포트를 제공합니다. 중간에 사용자가 개입하여 방향을 수정할 수도 있습니다.
