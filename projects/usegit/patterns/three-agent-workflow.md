# 패턴: Three-Agent Workflow — Claude + Gemini + Codex

> 설계일: 2026-03-08

---

## 역할 정의

```
Claude Code (Sonnet 4.6)      — 머리 (Orchestrator)
  ├── Gemini CLI (3.1 Pro)    — 분석손 (Analyst)
  └── Codex CLI  (gpt-5.4)   — 구현손 (Implementer)
```

| 역할 | 모델 | 특기 | 언제 |
|------|------|------|------|
| **머리** | Claude Sonnet 4.6 | 설계·판단·조율·최종검증 | 항상 |
| **분석손** | Gemini 3.1 Pro (`gemini-3.1-pro-preview`) | 1M 토큰 컨텍스트, 리서치, 전체 코드베이스 분석 | 대용량 분석 / 리서치 |
| **구현손** | gpt-5.4 extra high | 정밀 코드 생성·수정·실행 | 구현·파일 작성 |

---

## 호출 명령어

### Gemini (분석손)
```bash
# 기본 (비대화형)
gemini -m gemini-3.1-pro-preview --yolo -p "분석 지시"

# stdin으로 긴 프롬프트
gemini -m gemini-3.1-pro-preview --yolo -p - < task.md

# JSON 출력
gemini -m gemini-3.1-pro-preview --yolo --output-format json -p "분석 지시"
```

### Codex (구현손)
```bash
# 기본 (extra high reasoning)
codex exec --full-auto -C /path/to/project "구현 지시"

# 긴 프롬프트는 파일로
codex exec --full-auto -C /path/to/project - < task.md
```
> config.toml에 `model_reasoning_effort = "high"` 설정됨 (2026-03-08~)

### 병렬 실행 (git worktree 격리)
```bash
# worktree 생성
git worktree add /tmp/gemini-branch -b analysis/$(date +%s)
git worktree add /tmp/codex-branch  -b impl/$(date +%s)

# 병렬 dispatch
gemini -m gemini-3.1-pro-preview --yolo -p "..." > /tmp/gemini-result.md &
GEMINI_PID=$!

codex exec --full-auto -C /tmp/codex-branch "..." &
CODEX_PID=$!

wait $GEMINI_PID $CODEX_PID

# 완료 후 worktree 정리
git worktree remove /tmp/gemini-branch
git worktree remove /tmp/codex-branch
```

---

## 작업 분기 기준

```
머리(Claude)가 판단:

대용량 컨텍스트 필요?
  YES → Gemini (전체 코드베이스, 긴 로그, 문서 분석)
  NO  ↓

웹 리서치 / 최신 정보?
  YES → Gemini (Google 검색 연동)
  NO  ↓

코드 생성·수정·실행?
  YES → Codex (구현)
  NO  → Claude 직접 처리
```

---

## 프롬프트 구조

### Gemini에게
```
You are an analyst agent. Claude Code (Sonnet 4.6) is the orchestrator.

Task: [분석할 내용]
Scope: [파일/경로/주제 범위]
Output format: [원하는 출력 형식 — markdown / json / bullet list]
Done criteria: [완료 기준]
```

### Codex에게
```
You are a hands agent. Claude Code is the head.

Task: [구체적 구현 작업]
Path: [작업 경로]
Done criteria: [완료 기준 — 파일명, 테스트 통과 등]
```

---

## 실제 사용 예시

### 예시 1: 코드베이스 분석 후 구현
```bash
# 1단계: Gemini로 전체 분석
gemini -m gemini-3.1-pro-preview --yolo -p \
  "Analyze /home/tj/projects/autoai source code. List all API endpoints, their parameters, and return types. Output as JSON." \
  > /tmp/api-analysis.md

# 2단계: Claude가 분석 결과 검토 후 구현 지시
cat /tmp/api-analysis.md  # Claude가 읽고 판단

# 3단계: Codex로 구현
codex exec --full-auto -C /home/tj/projects/autoai \
  "Based on the API design, implement the missing /market/regime endpoint per spec in api-analysis.md"
```

### 예시 2: 병렬 — 분석 + 구현 동시
```bash
# Gemini: 현재 버그 원인 분석
gemini -m gemini-3.1-pro-preview --yolo -p "Read all files in /home/tj/projects/autoai/core/ and find the root cause of the NullPointerException in MarketAgent.run()" &

# Codex: 테스트 코드 작성 (독립 작업)
codex exec --full-auto -C /home/tj/projects/autoai "Write unit tests for collectors.py covering all edge cases" &

wait
```

---

## 설정 파일 현황

| 파일 | 설정 |
|------|------|
| `~/.codex/config.toml` | `model=gpt-5.4`, `reasoning_effort=high` |
| `~/.gemini/settings.json` | OAuth personal, preview features ON |
| Gemini 모델 | CLI 실행 시 `-m gemini-3.1-pro-preview` 플래그로 지정 |

---

## Gemini 실패 시 Fallback

`gemini-3.1-pro-preview`는 preview 모델 — 서버 용량 부족(429)이 발생할 수 있음.
**429 또는 rate limit 시 → Codex gpt-5.4로 대체 실행.**

```bash
# Gemini 시도 → 실패 시 Codex fallback
gemini -m gemini-3.1-pro-preview --approval-mode yolo -p - < task.md > /tmp/result.md 2>&1
if [ $? -ne 0 ] || grep -q "429\|rateLimitExceeded\|RESOURCE_EXHAUSTED" /tmp/result.md; then
    echo "[Fallback] Gemini 실패 → Codex gpt-5.4로 대체"
    codex exec --full-auto -C /path/to/project - < task.md > /tmp/result.md
fi
```

### Gemini vs Codex 능력 비교 (fallback 결정용)

| 기능 | Gemini 3.1 Pro | Codex gpt-5.4 |
|------|---------------|---------------|
| 컨텍스트 창 | 1M 토큰 | 제한적 |
| 웹/Google 검색 | ✅ 가능 | ❌ 불가 |
| 파일 시스템 읽기 | ✅ (workspace 내) | ✅ |
| 코드 실행 | ✅ | ✅ |
| 분석/리서치 | 매우 강함 | 강함 |
| 429 발생 가능성 | 있음 (preview) | 낮음 |

→ **웹 검색 불필요한 분석**이면 Codex fallback으로 동일한 결과 가능.
→ **최신 정보/Google 검색 필요** 시: 재시도하거나 Claude가 직접 처리.

### Gemini workspace 제한
- Gemini CLI는 파일 읽기를 프로젝트 디렉토리와 `~/.gemini/tmp/` 내로 제한
- `/tmp/` 경로의 파일을 Gemini에게 읽히려면 프로젝트 폴더에 복사 후 전달

```bash
# 올바른 방법: 프로젝트 내 임시 파일 사용
cp /tmp/codex_result.md /home/tj/projects/forecast/tmp_codex_result.md
gemini -m gemini-3.1-pro-preview --approval-mode yolo \
  -p "Read tmp_codex_result.md and prioritize by research impact"
rm /home/tj/projects/forecast/tmp_codex_result.md
```

---

## 주의사항

- Gemini `--yolo` → `--approval-mode yolo` (최신 CLI 플래그)
- worktree 병렬 실행 시 반드시 다른 브랜치 사용 (같은 파일 동시 수정 금지)
- Codex는 `workspace-write` 샌드박스 — 네트워크 접근 없음
- Gemini는 Google Search 연동 가능 (최신 정보 리서치에 활용)
- Gemini 429 → Codex 5.4 fallback (웹 검색 불필요 시 동등한 대체)
