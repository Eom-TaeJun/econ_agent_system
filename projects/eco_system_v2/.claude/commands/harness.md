---
description: "eco_system_v2의 harness 방향을 점검하고, 현재 작업에 필요한 문서/검증 경로를 정한다."
allowed-tools: ["Read", "Glob", "Grep", "Bash"]
---

# /harness — eco_system_v2 작업 방향 점검

## 읽을 파일

1. `CLAUDE.md`
2. `AGENTS.md`
3. `DOMAIN.md`
4. `docs/HARNESS_DIRECTION.md`

필요 시:

- `.claude/skills/domain-guide/SKILL.md`
- `.claude/skills/analysis-standards/SKILL.md`

## 해야 할 일

1. 현재 요청을 아래 셋 중 하나로 분류한다.
   - small fix
   - feature
   - structural change
2. 구조 문서 선수정이 필요한지 판단한다.
3. 필요한 verify 명령을 제시한다.
4. 작업이 길어질 경우 `docs/PROGRESS.md` 또는 `.harness/state.json` 사용 필요성을 말한다.

## 출력 형식

```text
작업 유형: feature
문서 수정 필요: 예 — agent 흐름이 바뀌므로 ARCHITECTURE 성격의 문서 필요
검증 명령:
- python main.py --quick
- python main.py --full
- python -m compileall domain/ agents/ infrastructure/
메모:
- domain purity 규칙 유지
- 여러 세션 작업이면 progress/state 기록 권장
```
