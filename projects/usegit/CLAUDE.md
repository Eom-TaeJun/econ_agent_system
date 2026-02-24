# usegit — 패턴 라이브러리

## 역할

Claude Code 작업 패턴, 워크플로우, 실전 경험을 축적하는 참조 저장소.

## 규칙

- `patterns/` 파일은 **읽기 전용** — 명시적 요청 없으면 수정 금지
- 새 패턴 추가 시: 실제 경험 기반일 것, 가설 기반 패턴 추가 금지
- 파일명 규칙: `kebab-case.md`

## 주요 패턴 파일

| 파일 | 내용 |
|------|------|
| `team-agents-workflow.md` | 머리/손 분업 워크플로우 |
| `hub-and-spoke.md` | 에이전트 조율 패턴 |
| `spec-driven-agent.md` | 스펙 기반 에이전트 설계 |
| `claude-md-guidelines.md` | CLAUDE.md 작성 지침 (논문 기반) |

## 새 패턴 추가 기준

실패 경험 → 규칙화 → patterns/ 저장. 이론만의 추가는 하지 않는다.
