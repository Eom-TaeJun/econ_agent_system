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
| `self` | `~/projects/self/` |
| `job-assistant` | `~/projects/job_assistant/` |
| `lm` | `~/projects/lm/` |

---

## 2. 역할 정의

| 단어 | 의미 | 모델 |
|------|------|------|
| `머리` | Claude Code — 설계, 판단, 조율 | Sonnet 4.6 |
| `구현손` | Codex CLI — 코드 구현, 파일 수정, 실행 | gpt-5.4 (extra high) |

---

## 3. Team Agents

구조: `머리 (Claude Code)` → `구현손 (Codex)`

**구현손 호출:**
```bash
codex exec --full-auto -C /path/to/project "작업 지시"
# config: gpt-5.4, reasoning_effort=high
```

**분기 기준:**
- 코드 구현 / 파일 수정 / 실행 → 구현손(Codex)
- 설계·판단·검증·리서치 → 머리(Claude)

**인증:**
- Codex: ChatGPT 로그인 (`codex login` → 브라우저 OAuth)
- Codex 캐시 꼬임 시: `rm ~/.codex/models_cache.json` 후 재실행

**상세 패턴:**
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
