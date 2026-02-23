# 작업 환경 규칙서

> Claude Code가 대화 시작 시 자동으로 읽는 설정 파일.

---

## 1. 경로 매핑

| 단어 | 경로 |
|------|------|
| `auth` | `~/projects/auth/` |
| `eimas` | `~/projects/autoai/eimas/` |
| `eco_system` | `~/projects/eco_system/` |
| `usegit` | `~/projects/usegit/` |
| `tech-digest` | `~/projects/tech-digest/` |
| `autoai` | `~/projects/autoai/` |
| `forecast` | `~/projects/forecast/` |
| `harness` | `~/projects/harness/` |
| `mlb-stats` | `~/projects/mlb-stats/` |

---

## 2. 역할 정의

| 단어 | 의미 |
|------|------|
| `머리` | Claude Code — 설계, 판단, 조율 |
| `손` | 서브에이전트 (general-purpose) — 파일 작성, 수정, 실행 |

---

## 3. Team Agents

구조: `머리 (Claude Code / Alpha)` → `손 (서브에이전트 / Beta)`

**팀 에이전트 작업 시작 전 반드시 읽을 것:**
→ `~/projects/usegit/patterns/team-agents-workflow.md`

---

## 4. 경량화 작업 규칙

작업 시 경량화했다면 반드시 문서화 (원본 / 뺀 것 / 이유).
저장 위치: `~/projects/usegit/patterns/` 또는 해당 프로젝트 CLAUDE.md

---

## 5. 작업 시작 체크리스트

팀 에이전트 스폰 전:
- [ ] 머리/손 역할 명시했는가?
- [ ] done criteria가 명확한가?
- [ ] 파일 충돌이 없는가?

경량화 작업 전:
- [ ] 원본 출처 파악했는가?
- [ ] 뺄 것/남길 것 결정했는가?
- [ ] 문서화 위치 정했는가?
