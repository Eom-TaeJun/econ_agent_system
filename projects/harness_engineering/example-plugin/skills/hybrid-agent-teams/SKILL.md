---
name: hybrid-agent-teams
description: |
  Claude Code Agent Teams + 멀티 AI 시스템(Perplexity/Gemini/Codex) 하이브리드 워크플로우.
  Claude Code 팀메이트 생성·관리, 다중 AI 병렬 개발, 작업별 AI 역할 분담 설계 시 활성화.
version: 1.0.0
updated: 2026-02-20
source: projects/autoai/HYBRID_AGENT_TEAMS.md
---

# Hybrid Agent Teams 표준

## 아키텍처 개념

```
멀티 AI 시스템 (상위)
    ├─> Perplexity Agent (리서치)
    ├─> Gemini Agent (데이터 수집)
    ├─> Codex Agent (코드 생성)
    └─> Claude Code Agent Teams (하위 — 복잡한 구현)
           ├─> Lead (아키텍처 설계)
           ├─> Teammate 1 (코드 리뷰)
           ├─> Teammate 2 (테스트 작성)
           └─> Teammate 3 (문서화)
```

**핵심 원칙:**
- Codex는 Agent Teams에 직접 추가 불가 (Claude만 가능)
- 멀티 AI 시스템과 Agent Teams를 병렬로 운영 가능

## 활성화 설정

```bash
# 환경 변수 (임시)
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# 영구 설정 (~/.claude/settings.json)
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## 작업별 AI 역할 매트릭스

| 작업 유형 | 담당 AI | 이유 |
|----------|---------|------|
| 리서치/정보 수집 | Perplexity | 저렴 + 빠름 |
| 대량 데이터 처리 | Gemini | 긴 컨텍스트 |
| 보일러플레이트 코드 | Codex | 빠름 |
| 간단한 작업 리뷰 | Claude Haiku | 저렴 |
| 복잡한 구현·리팩토링 | Claude Teams | 강력 + 병렬 |

## 주요 사용 패턴

### 패턴 1: 리서치 → 구현 분리
```python
# 1. Perplexity가 리서치 (빠르고 정확)
research = await perplexity_agent.process(query)

# 2. Claude Code Agent Teams로 구현
# 터미널에서: claude code
# Lead에게: "Implement the following based on research: ..."
```

### 패턴 2: 코드 생성 → 멀티 리뷰
```python
# 1. Codex가 초안 생성
draft_code = await codex_agent.process(task)

# 2. Claude Teams가 병렬 리뷰
# Teammate 1: 보안 리뷰
# Teammate 2: 성능 리뷰
# Teammate 3: 가독성 리뷰
```

### 패턴 3: 병렬 모듈 개발
```python
results = await asyncio.gather(
    perplexity_agent.research_module(),   # 리서치
    codex_agent.generate_collectors(),   # 데이터 수집
    gemini_agent.process_large_dataset() # 대량 데이터
    # Claude Teams는 코어 로직 (별도 터미널)
)
```

## Claude Code Agent Teams 명령어

```
# Lead 명령어
/create-teammate "description"  # 새 teammate 생성
/shutdown-teammate <id>         # teammate 종료
/message-teammate <id> "msg"   # 특정 teammate 메시지
/list-teammates                 # 모든 teammates 목록

# 작업 관리
TaskCreate    # 새 작업 생성
TaskUpdate    # 작업 상태 업데이트 (in_progress → completed)
TaskList      # 작업 목록 확인

# 화면 전환 (in-process 모드)
Shift + ↑  # 이전 teammate
Shift + ↓  # 다음 teammate
```

## 실전 시나리오

### 대규모 리팩토링
```bash
# 터미널 1: 멀티 AI 분석
python main.py --analyze-codebase

# 터미널 2: Claude Code Teams 구현
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
claude code
# Lead: "Create 3 teammates to refactor:
#   - Teammate 1: core/message_bus.py
#   - Teammate 2: agents/base_agent.py
#   - Teammate 3: workflows/"
```

### 비용 최적화 기준
```python
# 작업 복잡도 기반 선택
def choose_ai(complexity: int) -> str:
    if complexity >= 7:   return "claude_teams"   # 병렬 처리 필요
    elif complexity >= 4: return "claude_solo"    # Claude 단독
    else:                 return "codex"          # 빠른 생성
```

## tmux 하이브리드 설정

```bash
# 세션 생성 (hybrid-ai-dev.sh)
tmux new-session -d -s hybrid-ai
# 윈도우 1: 멀티 AI (Perplexity/Gemini/Codex)
# 윈도우 2: Claude Code Agent Teams
# 윈도우 3: git status 모니터링
```

## 비용 모니터링 기준

```python
cost_matrix = {
    'perplexity': 0.001,      # per call
    'codex':      0.002,      # per call
    'gemini':     0.001,      # per call
    'haiku':      0.001,      # per call (simple review)
    'claude_teams': 0.015     # per teammate
}
# → Claude Teams는 복잡한 작업에만 사용
```

---
상세 내용: `references/hybrid-teams-guide.md`
원본 위치: `projects/autoai/HYBRID_AGENT_TEAMS.md`
