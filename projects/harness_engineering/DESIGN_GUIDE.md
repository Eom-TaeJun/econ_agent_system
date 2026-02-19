# 하니스 엔지니어링: Skill / MCP / Agent 설계 가이드

> Claude Code 플러그인 생태계를 하니스 관점으로 설계하는 방법

---

## 1. 개념 매핑: 하니스 컴포넌트 → Claude Code 구성요소

하니스 엔지니어링의 각 레이어가 Claude Code에서 어떻게 구현되는지 매핑한다.

```
┌─────────────────────────────────────────────────────────┐
│                   사용자 인터페이스                        │
│                  Commands (Slash /)                       │
├─────────────────────────────────────────────────────────┤
│               자율 실행 레이어 (Reasoning)                 │
│                Agents (Subagents)                         │
├───────────────────────────┬─────────────────────────────┤
│    지식/컨텍스트 레이어     │    외부 서비스 연결 레이어     │
│    Skills (Auto-activate) │    MCP Servers               │
├───────────────────────────┴─────────────────────────────┤
│              가드레일 & 이벤트 레이어                      │
│                    Hooks                                  │
└─────────────────────────────────────────────────────────┘
```

| 하니스 개념 | Claude Code 구성요소 | 역할 |
|------------|---------------------|------|
| 컨텍스트 주입 | **Skill** | 모델에게 언제 어떤 지식을 줄지 자동 결정 |
| 툴 통합 레이어 | **MCP Server** | 외부 API/DB/서비스를 툴로 노출 |
| 자율 실행 에이전트 | **Agent** | 복잡한 다단계 작업을 독립 처리 |
| 가드레일 & 검증 | **Hook** | 이벤트 기반 자동 검증/차단/컨텍스트 보강 |
| 사용자 진입점 | **Command** | 재사용 가능한 워크플로우 슬래시 커맨드 |
| 설정 & 조율 | **plugin.json** | 전체 하니스의 매니페스트 |

---

## 2. 플러그인 = 하나의 하니스 단위

### 디렉토리 구조 (하니스 관점)

```
my-harness-plugin/
├── .claude-plugin/
│   └── plugin.json          # 하니스 매니페스트
│
├── commands/                 # 사용자 진입점
│   ├── analyze.md           # /analyze → Agent 실행 트리거
│   └── report.md            # /report → Skill + MCP 조합
│
├── agents/                   # 자율 실행 단위
│   ├── deep-analyzer.md     # 심층 분석 에이전트
│   └── report-writer.md     # 리포트 생성 에이전트
│
├── skills/                   # 컨텍스트 주입 단위 (자동 활성화)
│   ├── domain-knowledge/
│   │   └── SKILL.md         # 도메인 지식 자동 주입
│   └── output-standards/
│       └── SKILL.md         # 출력 형식 표준 자동 적용
│
├── hooks/                    # 가드레일
│   ├── hooks.json           # 이벤트 핸들러 설정
│   └── scripts/
│       ├── validate.sh      # PreToolUse 검증
│       └── load-context.sh  # SessionStart 컨텍스트 로드
│
└── .mcp.json                # 외부 서비스 연결
```

---

## 3. Skill: 컨텍스트 자동 주입 레이어

### 핵심 개념

Skill은 **능동적으로 트리거되지 않는다**. Claude가 작업 컨텍스트를 보고 **자동으로 활성화**한다.
하니스 관점에서 Skill은 "Context Retrieval" — 필요한 시점에 관련 지식을 동적 주입하는 메커니즘이다.

### SKILL.md 파일 형식

```markdown
---
name: skill-name
description: |
  이 스킬이 언제 활성화되어야 하는지 명확히 서술.
  Claude가 이 description을 읽고 상황에 맞는지 판단한다.
  구체적일수록 정확한 타이밍에 활성화된다.
version: 1.0.0
---

# 스킬 본문

Claude에게 주입할 지식, 가이드라인, 절차를 여기에 작성.
```

### 설계 원칙

**1. description이 트리거다**
```markdown
---
description: |
  이코노믹스 데이터 분석, FRED API 데이터 처리, 거시경제 지표 해석,
  GDP/인플레이션/실업률 시계열 분석 작업 시 활성화된다.
  단순한 수치 계산이나 비경제적 데이터 분석에는 사용하지 않는다.
---
```

**2. 스킬 내용은 Claude의 행동 지침**
```markdown
# 경제 데이터 분석 표준

## 데이터 검증 절차
1. 시계열 연속성 확인 (결측값, 이상치)
2. 단위 일관성 검사 (명목/실질, 계절조정 여부)
3. 출처 메타데이터 기록

## 해석 가이드라인
- 상관관계와 인과관계를 명확히 구분
- 95% 신뢰구간 항상 보고
- 정책적 함의 서술 시 근거 명시
```

**3. references/ 에 보조 자료 연결**
```
skills/
└── econ-analysis/
    ├── SKILL.md
    ├── references/
    │   ├── fred-api-spec.md    # API 사양
    │   └── indicator-glossary.md  # 지표 용어 사전
    └── examples/
        └── analysis-template.md
```

### Skill이 하니스에서 하는 일

```
사용자: "GDP 성장률 분석해줘"
         ↓
Claude: task context 확인
         ↓
Skill description 매칭: "경제 데이터 분석" 해당
         ↓
SKILL.md 내용이 context에 자동 주입
         ↓
Claude: 표준 절차에 따라 분석 수행
```

---

## 4. MCP Server: 외부 서비스 툴 통합 레이어

### 핵심 개념

MCP는 **외부 세계와의 연결**이다. Claude가 직접 접근하지 못하는 DB, API, 파일시스템을
툴(tool call)로 제공한다. 하니스의 "Tool Integration Layer" 역할.

### .mcp.json 설정 형식

```json
{
  "mcpServers": {
    "서버-이름": {
      "command": "실행 명령",
      "args": ["인수들"],
      "env": {
        "API_KEY": "${환경변수}"
      }
    }
  }
}
```

### 4가지 연결 타입

#### stdio (로컬 프로세스) - 커스텀 서버, 로컬 DB
```json
{
  "my-db": {
    "command": "python",
    "args": ["-m", "my_mcp_server"],
    "env": {
      "DATABASE_URL": "${DATABASE_URL}"
    }
  }
}
```

#### SSE (Server-Sent Events) - OAuth 인증이 필요한 클라우드 서비스
```json
{
  "github": {
    "type": "sse",
    "url": "https://mcp.github.com/sse"
  }
}
```

#### HTTP (REST API) - 토큰 기반 API
```json
{
  "my-api": {
    "type": "http",
    "url": "https://api.example.com/mcp",
    "headers": {
      "Authorization": "Bearer ${API_TOKEN}"
    }
  }
}
```

#### WebSocket - 실시간 스트리밍
```json
{
  "realtime": {
    "type": "ws",
    "url": "wss://stream.example.com/ws"
  }
}
```

### MCP 툴 네이밍 규칙

MCP 툴은 자동으로 네임스페이싱된다:
```
mcp__plugin_{플러그인명}_{서버명}__{툴명}
예: mcp__plugin_fred_fred-api__get_series_data
```

커맨드에서 특정 툴만 허용할 때:
```markdown
---
allowed-tools: [
  "mcp__plugin_fred_fred-api__get_series_data",
  "mcp__plugin_fred_fred-api__search_series"
]
---
```

### MCP 서버 직접 구현 (Python 예시)

```python
# my_mcp_server.py
from mcp import Server, Tool
import json

server = Server("my-data-server")

@server.tool("fetch_data")
async def fetch_data(query: str, limit: int = 100) -> dict:
    """데이터베이스에서 데이터를 가져옵니다"""
    # 실제 DB 조회 로직
    results = db.query(query, limit=limit)
    return {"data": results, "count": len(results)}

if __name__ == "__main__":
    server.run_stdio()
```

---

## 5. Agent: 자율 실행 레이어

### 핵심 개념

Agent는 **독립적인 서브프로세스**로 복잡한 다단계 작업을 처리한다.
부모 컨텍스트와 분리된 자체 컨텍스트 윈도우를 갖는다.
하니스의 "Sub-agent Coordination" 역할.

### Agent 파일 형식

```markdown
---
name: agent-identifier
description: |
  Use this agent when [명확한 트리거 조건].

  <example>
  Context: [상황 설명]
  user: "[사용자 요청]"
  assistant: "[에이전트를 어떻게 사용할지]"
  <commentary>
  [이 에이전트가 선택되어야 하는 이유]
  </commentary>
  </example>

model: inherit        # inherit | sonnet | opus | haiku
color: blue           # blue | cyan | green | yellow | magenta | red
tools: ["Read", "Write", "Grep", "Bash"]  # 최소 권한 원칙
---

# Agent 시스템 프롬프트

You are [역할 설명] specializing in [도메인].

**Core Responsibilities:**
1. [주요 책임 1]
2. [주요 책임 2]

**Process:**
1. [단계 1]
2. [단계 2]
3. [단계 3]

**Output Format:**
[출력 형식 정의]
```

### Agent vs Command 선택 기준

| 상황 | 선택 |
|------|------|
| 사용자가 직접 시작하는 작업 | **Command** |
| 자율적으로 판단해서 실행하는 작업 | **Agent** |
| 단순한 템플릿 실행 | **Command** |
| 수십 개 파일을 탐색하고 판단하는 분석 | **Agent** |
| 결과를 빠르게 반환 | **Command** |
| 수시간이 걸릴 수 있는 작업 | **Agent** |

### Agent 설계 원칙

**1. description에 예시를 2-4개 포함**
```markdown
description: |
  Use this agent when analyzing economic data that requires
  multi-step validation and cross-indicator correlation.

  <example>
  Context: 사용자가 최근 5년간 GDP-실업률 관계 분석 요청
  user: "GDP와 실업률 상관관계를 분석해줘"
  assistant: "econ-analyzer 에이전트로 심층 분석을 시작합니다."
  <commentary>
  단순 계산이 아닌 다단계 통계 분석이 필요하므로 에이전트 사용
  </commentary>
  </example>
```

**2. 최소 권한 원칙 (tools 제한)**
```markdown
# 읽기 전용 분석 에이전트
tools: ["Read", "Grep", "Glob"]

# 코드 생성 에이전트
tools: ["Read", "Write", "Edit", "Grep"]

# 테스트 실행 에이전트
tools: ["Read", "Bash", "Grep"]
```

**3. 컬러 코드 의미 통일**
```
blue/cyan   → 분석, 리뷰 에이전트
green       → 생성, 빌드 에이전트
yellow      → 검증, 경고 에이전트
red         → 보안, 위험 검사 에이전트
magenta     → 창작, 문서 생성 에이전트
```

---

## 6. Hook: 가드레일 & 이벤트 레이어

### 핵심 개념

Hook은 **하니스의 안전망**이다. Claude가 행동하기 전/후에 자동으로 실행되어
검증, 차단, 컨텍스트 보강을 담당한다. 하니스의 "Verification & Guardrails" 역할.

### hooks.json 형식 (플러그인용)

```json
{
  "description": "플러그인 훅 설명",
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Stop": [...],
    "SessionStart": [...],
    "UserPromptSubmit": [...]
  }
}
```

### 주요 이벤트와 활용

#### PreToolUse - 툴 실행 전 검증/차단
```json
{
  "PreToolUse": [{
    "matcher": "Write|Edit",
    "hooks": [{
      "type": "prompt",
      "prompt": "파일 쓰기 작업 검증: 시스템 파일(.env, /etc/), 민감 정보(API 키, 패스워드) 접근 여부 확인. 문제없으면 'approve', 위험하면 'deny' 반환."
    }]
  }, {
    "matcher": "Bash",
    "hooks": [{
      "type": "command",
      "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate-bash.sh",
      "timeout": 10
    }]
  }]
}
```

#### Stop - 완료 검증 (작업 완성도 보장)
```json
{
  "Stop": [{
    "matcher": "*",
    "hooks": [{
      "type": "prompt",
      "prompt": "작업 완료 검증: 요청된 모든 항목이 처리되었는지, 테스트가 실행되었는지, 사용자 질문에 답변했는지 확인. 완료되면 'approve', 미완료 항목이 있으면 'block'과 이유 반환."
    }]
  }]
}
```

#### SessionStart - 세션 시작 시 컨텍스트 로드
```json
{
  "SessionStart": [{
    "matcher": "*",
    "hooks": [{
      "type": "command",
      "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/load-context.sh",
      "timeout": 15
    }]
  }]
}
```

```bash
#!/bin/bash
# load-context.sh - 프로젝트 컨텍스트 환경변수로 설정
PROJECT_CONFIG="$CLAUDE_PROJECT_DIR/.project-config.json"

if [ -f "$PROJECT_CONFIG" ]; then
  PROJECT_TYPE=$(jq -r '.type' "$PROJECT_CONFIG")
  echo "export PROJECT_TYPE=$PROJECT_TYPE" >> "$CLAUDE_ENV_FILE"
  echo "프로젝트 타입 로드: $PROJECT_TYPE"
fi
```

#### PreCompact - 컨텍스트 압축 전 중요 정보 보존
```json
{
  "PreCompact": [{
    "matcher": "*",
    "hooks": [{
      "type": "prompt",
      "prompt": "컨텍스트 압축 전: 완료된 마일스톤, 핵심 결정사항, 다음 단계를 systemMessage에 요약해서 압축 후에도 유지되도록 한다."
    }]
  }]
}
```

### Prompt-based vs Command Hook 선택

| 상황 | Hook 타입 |
|------|----------|
| 복잡한 맥락 판단 필요 | **prompt** |
| 빠른 결정론적 검사 | **command** |
| 파일 경로 검증 | **command** |
| 의도 파악 후 허용/차단 | **prompt** |
| 환경변수 설정 | **command** |

---

## 7. Command: 사용자 진입점 레이어

### 핵심 개념

Command는 **Claude에게 내리는 지시문**이다. 사용자가 `/command`를 입력하면 이 파일의
내용이 Claude의 지시로 변환된다. 하니스의 진입점(Entry Point).

### Command 파일 형식

```markdown
---
description: 커맨드 설명 (60자 이내, /help에 표시됨)
argument-hint: [인수1] [인수2]
allowed-tools: Read, Write, Bash(git:*)
model: inherit
---

<!-- 이 아래는 Claude에게 전달되는 지시문 -->

$1 파일에 대해 다음을 수행하라:
1. 코드 품질 분석
2. 보안 취약점 검사
3. 리포트 생성
```

### 동적 요소 활용

```markdown
---
description: 경제 분석 실행
argument-hint: [지표명] [기간]
allowed-tools: Read, Bash(python:*)
---

!`python ${CLAUDE_PLUGIN_ROOT}/scripts/validate-indicator.py $1`

$1 지표의 $2 기간 데이터를 분석하라:
1. 데이터 수집: @${CLAUDE_PLUGIN_ROOT}/config/indicators.json 참조
2. deep-analyzer 에이전트로 심층 분석 실행
3. output-standards 스킬에 따라 리포트 작성
```

### Multi-component Workflow Command

Agent + Skill + MCP를 조합하는 커맨드:

```markdown
---
description: 전체 분석 파이프라인 실행
argument-hint: [프로젝트명]
allowed-tools: Read, Write, Bash(python:*)
---

프로젝트 $1 분석 파이프라인:

**Phase 1 - 데이터 수집**
MCP 서버를 통해 $1 관련 데이터 수집

**Phase 2 - 심층 분석**
deep-analyzer 에이전트를 사용해 데이터 분석 수행

**Phase 3 - 리포트 생성**
report-writer 에이전트로 최종 리포트 작성
출력 표준: @${CLAUDE_PLUGIN_ROOT}/templates/report-template.md 준수

결과를 outputs/ 폴더에 저장하라.
```

---

## 8. 전체 설계 플로우

### 프로젝트별 하니스 설계 절차

```
1. 도메인 지식 파악
   └→ Skills로 구현 (자동 컨텍스트 주입)

2. 외부 연결 필요성 파악
   └→ MCP Servers로 구현 (툴 통합)

3. 복잡한 자율 작업 파악
   └→ Agents로 구현 (다단계 실행)

4. 안전/검증 필요성 파악
   └→ Hooks로 구현 (가드레일)

5. 사용자 진입점 설계
   └→ Commands로 구현 (워크플로우 트리거)

6. 전체 조율
   └→ plugin.json으로 통합
```

### 실제 예시: 경제 분석 하니스

```
사용자: /analyze gdp 2020-2024
         ↓
Command: analyze.md 실행
         ↓
MCP: fred-api 서버로 GDP 데이터 수집
         ↓
Skill: econ-analysis 자동 활성화 (분석 표준 주입)
         ↓
Agent: deep-analyzer 실행 (다단계 통계 분석)
         ↓
Hook (Stop): 분석 완료 검증
         ↓
Agent: report-writer 실행 (리포트 생성)
         ↓
Hook (PostToolUse/Write): 파일 쓰기 검증
         ↓
완성된 리포트 출력
```

---

## 9. 각 컴포넌트별 파일 예시 (최소 구현)

### Skill 최소 예시

```markdown
<!-- skills/my-domain/SKILL.md -->
---
name: my-domain
description: |
  [도메인 관련] 작업 시 활성화. 구체적 트리거 조건 작성.
version: 1.0.0
---

# 도메인 지식

여기에 Claude에게 주입할 내용 작성.
```

### Agent 최소 예시

```markdown
<!-- agents/my-agent.md -->
---
name: my-agent
description: |
  Use this agent when [트리거 조건].
  <example>
  Context: [상황]
  user: "[요청]"
  assistant: "[응답 방식]"
  <commentary>[이유]</commentary>
  </example>
model: inherit
color: blue
tools: ["Read", "Grep"]
---

You are [역할]. Process: 1. [단계1] 2. [단계2]
Output: [형식]
```

### MCP 최소 예시

```json
// .mcp.json
{
  "mcpServers": {
    "my-service": {
      "command": "python",
      "args": ["-m", "my_mcp_server"],
      "env": { "API_KEY": "${MY_API_KEY}" }
    }
  }
}
```

### Hook 최소 예시

```json
// hooks/hooks.json
{
  "hooks": {
    "Stop": [{
      "matcher": "*",
      "hooks": [{
        "type": "prompt",
        "prompt": "작업이 완전히 완료되었는지 확인. 완료: 'approve', 미완료: 'block' + 이유"
      }]
    }]
  }
}
```

### Command 최소 예시

```markdown
<!-- commands/my-command.md -->
---
description: 커맨드 설명
argument-hint: [인수]
---

$1에 대해 분석하고 결과를 출력하라.
```

### plugin.json 최소 예시

```json
{
  "name": "my-harness-plugin",
  "version": "1.0.0",
  "description": "하니스 엔지니어링 기반 플러그인"
}
```

---

## 10. 하니스 품질 체크리스트

### Skill
- [ ] description이 구체적 트리거 조건을 서술하는가
- [ ] 언제 활성화되지 않아야 하는지도 명시했는가
- [ ] references/ 에 보조 자료가 연결되었는가

### MCP Server
- [ ] `${CLAUDE_PLUGIN_ROOT}` 를 절대경로 대신 사용했는가
- [ ] 환경변수로 자격증명을 관리하는가
- [ ] Command의 `allowed-tools` 에 필요한 툴만 명시했는가
- [ ] 에러 핸들링이 있는가 (연결 실패, 툴 호출 실패)

### Agent
- [ ] description에 2-4개의 구체적 예시가 있는가
- [ ] `tools` 를 최소 권한으로 제한했는가
- [ ] 시스템 프롬프트가 역할, 절차, 출력형식을 정의하는가
- [ ] Command와 중복 없이 역할이 구분되는가

### Hook
- [ ] `${CLAUDE_PLUGIN_ROOT}` 경로를 사용했는가
- [ ] 타임아웃이 설정되었는가
- [ ] Stop 훅으로 작업 완성도를 검증하는가
- [ ] SessionStart 훅으로 필요한 컨텍스트를 로드하는가

### Command
- [ ] 지시문이 Claude를 대상으로 작성되었는가 (사용자 대상 아님)
- [ ] `allowed-tools` 로 필요한 권한만 명시했는가
- [ ] `argument-hint` 로 사용법을 문서화했는가
- [ ] 복잡한 작업은 Agent에 위임하고 있는가

---

## 참고 문서

- [하니스 엔지니어링 개요](./README.md)
- [Plugin Structure SKILL](~/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/skills/plugin-structure/SKILL.md)
- [Agent Development SKILL](~/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/skills/agent-development/SKILL.md)
- [MCP Integration SKILL](~/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/skills/mcp-integration/SKILL.md)
- [Command Development SKILL](~/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/skills/command-development/SKILL.md)
- [Hook Development SKILL](~/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/skills/hook-development/SKILL.md)
