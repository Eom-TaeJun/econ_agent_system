# Hybrid Agent Teams - Claude Code + 멀티 AI 시스템

## 개념: 두 시스템을 함께 활용

### 아키텍처
```
당신의 멀티 AI 시스템 (상위 레벨)
    ├─> Perplexity Agent (리서치)
    ├─> Gemini Agent (데이터 수집)
    ├─> Codex Agent (코드 생성)
    └─> Claude Code Agent Teams (하위 레벨)
           ├─> Lead (아키텍처 설계)
           ├─> Teammate 1 (코드 리뷰)
           ├─> Teammate 2 (테스트 작성)
           └─> Teammate 3 (문서화)
```

## 설정 방법

### 1. Claude Code Agent Teams 활성화
```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# 적용
source ~/.bashrc
```

### 2. 설정 파일로 영구 활성화
```json
// ~/.claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "agentTeams": {
    "enabled": true,
    "displayMode": "split-pane",  // or "in-process"
    "maxTeammates": 4,
    "autoShutdownOnIdle": true
  }
}
```

### 3. 확인
```bash
claude code

# Lead가 활성화되었는지 확인
# /help 명령어로 teammate 관련 명령어 확인
```

## 사용 패턴

### 패턴 1: 리서치는 Perplexity, 구현은 Claude Teams
```python
# autoai/econ_agent_system/main.py

async def hybrid_workflow(query: str):
    # 1. Perplexity가 리서치 (빠르고 정확)
    research = await perplexity_agent.process(query)

    # 2. Claude Code Agent Teams로 구현 위임
    # (터미널에서 수동으로 Claude Code 실행)
    print("Research completed. Results:")
    print(research)
    print("\n💡 Now switch to Claude Code with Agent Teams enabled")
    print("Task: Implement the following architecture...")

    # 또는 subprocess로 Claude Code 실행
    implementation = await spawn_claude_code_team(
        task=f"Implement: {research['architecture']}",
        teammates=3
    )

    return {
        'research': research,
        'implementation': implementation
    }
```

### 패턴 2: 코드 생성은 Codex, 리뷰는 Claude Teams
```python
async def code_review_workflow(task: str):
    # 1. Codex가 빠르게 초안 생성
    draft_code = await codex_agent.process(task)

    # 2. Claude Teams가 다각도 리뷰
    with claude_code_teams(num_reviewers=3):
        # Lead: 전체 조율
        # Teammate 1: 보안 리뷰
        # Teammate 2: 성능 리뷰
        # Teammate 3: 가독성 리뷰

        reviews = await parallel_review(
            code=draft_code,
            aspects=['security', 'performance', 'readability']
        )

    return integrate_feedback(draft_code, reviews)
```

### 패턴 3: 각 AI가 독립 모듈, Claude Teams가 통합
```python
async def parallel_module_development():
    # 병렬로 각 AI가 담당
    results = await asyncio.gather(
        perplexity_agent.research_module(),     # 리서치
        codex_agent.generate_collectors(),      # 데이터 수집
        gemini_agent.process_large_dataset(),   # 대량 데이터
        # Claude Teams는 코어 로직 개발 (별도 프로세스)
    )

    # Claude Code Agent Teams (별도 세션)
    # Lead: core/message_bus.py 리팩토링
    # Teammate 1: core/base_agent.py 개선
    # Teammate 2: workflows/ 업데이트
    # Teammate 3: 통합 테스트

    return combine_modules(results)
```

## 실전 설정

### Step 1: 환경 설정
```bash
# 1. Claude Code Agent Teams 활성화
cat >> ~/.bashrc << 'EOF'
# Agent Teams 설정
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
EOF

source ~/.bashrc

# 2. tmux 설치 (split-pane 모드용)
sudo apt-get install tmux

# 3. 설정 확인
claude code  # Agent Teams 메시지가 보이는지 확인
```

### Step 2: 작업 시나리오별 전략

#### 시나리오 A: 대규모 리팩토링
```bash
# 터미널 1: 멀티 AI 시스템 (분석)
cd /home/tj/projects/autoai/econ_agent_system
python main.py --analyze-codebase

# 터미널 2: Claude Code Agent Teams (구현)
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
cd /home/tj/projects/autoai/econ_agent_system
claude code

# Lead에게 지시:
"Create 3 teammates to refactor the agent system:
- Teammate 1: Refactor core/message_bus.py
- Teammate 2: Improve agents/base_agent.py
- Teammate 3: Update all agent implementations"
```

#### 시나리오 B: 새 기능 개발
```bash
# 1. Perplexity로 리서치
cd /home/tj/projects/autoai
python -c "
from agents.perplexity_agent import PerplexityAgent
agent = PerplexityAgent()
result = agent.research('Latest multi-agent frameworks 2026')
print(result)
"

# 2. Claude Code Agent Teams로 구현
claude code
# "Implement the findings from research: [paste results]
#  Use 3 teammates for parallel development"

# 3. Codex로 보일러플레이트 생성
codex
# "Generate API client boilerplate for the new framework"
```

#### 시나리오 C: 버그 수정 + 테스트
```bash
# 터미널 1: Claude Code Agent Teams
claude code
# Lead가 버그 분석
# Teammate 1이 수정
# Teammate 2가 테스트 작성
# Teammate 3이 문서 업데이트

# 터미널 2: 외부 AI 에이전트들
python main.py --validate-fix
```

### Step 3: 자동화 스크립트

```bash
# ~/scripts/hybrid-ai-dev.sh
#!/bin/bash

PROJECT_DIR="${1:-/home/tj/projects/autoai}"
TASK="${2:-development}"

echo "🤖 Hybrid AI Development System"
echo "================================"

# tmux 세션 생성
tmux new-session -d -s hybrid-ai -c "$PROJECT_DIR"

# 윈도우 1: 멀티 AI 시스템
tmux rename-window -t hybrid-ai:0 'Multi-AI'
tmux send-keys -t hybrid-ai:0 "echo '🌐 Multi-AI Agents (Perplexity, Gemini, Codex)'" C-m
tmux send-keys -t hybrid-ai:0 "python main.py --interactive" C-m

# 윈도우 2: Claude Code Agent Teams
tmux new-window -t hybrid-ai:1 -n 'Claude-Teams' -c "$PROJECT_DIR"
tmux send-keys -t hybrid-ai:1 "export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1" C-m
tmux send-keys -t hybrid-ai:1 "echo '👥 Claude Code Agent Teams'" C-m
tmux send-keys -t hybrid-ai:1 "claude code" C-m

# 윈도우 3: 모니터링
tmux new-window -t hybrid-ai:2 -n 'Monitor' -c "$PROJECT_DIR"
tmux send-keys -t hybrid-ai:2 "watch -n 2 'git status --short'" C-m

# 연결
tmux select-window -t hybrid-ai:0
tmux attach-session -t hybrid-ai
```

```bash
# 실행
chmod +x ~/scripts/hybrid-ai-dev.sh
~/scripts/hybrid-ai-dev.sh /home/tj/projects/autoai
```

## Agent Teams 명령어

### Lead (조율자) 명령어
```
/create-teammate "description"  # 새 teammate 생성
/shutdown-teammate <id>         # teammate 종료
/message-teammate <id> "msg"   # 특정 teammate에게 메시지
/list-teammates                 # 모든 teammates 목록
/switch-to-teammate <id>       # teammate 화면으로 전환
```

### 작업 관리
```
/tasks                          # 작업 목록 확인
/claim-task <id>               # 작업 할당
TaskCreate                     # 새 작업 생성 (tool)
TaskUpdate                     # 작업 상태 업데이트 (tool)
```

### 화면 전환 (in-process 모드)
```
Shift + ↑  # 이전 teammate
Shift + ↓  # 다음 teammate
```

## 비용 최적화

### 전략 1: 작업별 최적 AI 선택
```python
cost_matrix = {
    'research': 'perplexity',      # 저렴 + 빠름
    'code_gen': 'codex',            # 중간
    'simple_review': 'haiku',       # 저렴
    'complex_analysis': 'claude_teams',  # 비쌈 but 강력
    'data_processing': 'gemini'     # 중간
}

# 비용 모니터링
async def monitor_costs():
    costs = {
        'perplexity': count * 0.001,
        'codex': count * 0.002,
        'claude_teams': teammates * 0.015,  # per teammate
        'gemini': count * 0.001
    }
    return sum(costs.values())
```

### 전략 2: Claude Teams는 복잡한 작업만
```python
def should_use_claude_teams(task_complexity: int) -> bool:
    """
    복잡도가 높은 작업만 Claude Teams 사용
    """
    thresholds = {
        'simple': (1, 3),      # Codex 단독
        'medium': (4, 6),      # Claude 단독
        'complex': (7, 10)     # Claude Teams
    }

    if task_complexity >= 7:
        return True  # Claude Teams (병렬 처리 필요)
    elif task_complexity >= 4:
        return False  # Claude 단독
    else:
        return False  # Codex 단독
```

## 성공 지표

### 1주차: 설정 및 탐색
- [ ] Agent Teams 활성화 확인
- [ ] Teammate 생성/관리 테스트
- [ ] 멀티 AI 시스템과 연동 테스트

### 2주차: 실전 적용
- [ ] 실제 프로젝트에서 hybrid 워크플로우 사용
- [ ] 작업별 최적 AI 선택 패턴 확립
- [ ] 비용 트래킹 시작

### 4주차: 최적화
- [ ] 워크플로우 자동화 스크립트 완성
- [ ] 생산성 30%+ 향상 달성
- [ ] 비용 효율성 측정 및 개선

## 트러블슈팅

### 문제: Agent Teams가 활성화 안 됨
```bash
# 확인
echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS

# 해결
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
source ~/.bashrc
```

### 문제: Teammates가 너무 많은 비용
```bash
# 해결: 복잡한 작업만 teammates 사용
# 단순 작업은 멀티 AI 시스템으로
```

### 문제: 컨텍스트 공유 어려움
```bash
# 해결: 공유 파일 사용
echo "Current context" > .dev-context.md
# 모든 AI가 이 파일 참조
```

## 요약

| 기능 | Claude Code Agent Teams | 멀티 AI 시스템 | Hybrid |
|-----|------------------------|---------------|---------|
| **활성화** | `EXPERIMENTAL_AGENT_TEAMS=1` | 직접 구현 | 둘 다 |
| **AI 종류** | Claude만 | 모든 AI | 모든 AI |
| **병렬 처리** | ✅ 자동 | ✅ 수동 | ✅ 최적 |
| **비용** | 높음 | 중간 | 최적화 가능 |
| **복잡도** | 낮음 | 높음 | 중간 |
| **추천 사용** | 복잡한 개발 | 다양한 AI 필요 | 대규모 프로젝트 |

---

**핵심 포인트:**
1. ✅ Agent Teams는 Claude Code 빌트인 기능 (환경변수로 활성화)
2. ✅ Codex는 Agent Teams에 직접 추가 불가 (Claude만 가능)
3. ✅ **하지만** 멀티 AI 시스템과 Agent Teams를 함께 사용 가능!
4. 🎯 최적 전략: 리서치/데이터는 Perplexity/Gemini/Codex, 복잡한 개발은 Claude Teams
