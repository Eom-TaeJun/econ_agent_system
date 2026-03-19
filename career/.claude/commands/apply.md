---
description: "career 작업공간에서 어떤 역할부터 실행할지 정하는 진입 명령이다."
allowed-tools: ["Read", "Glob", "Grep"]
---

# /apply — career 문서 작성 시작

## 읽을 파일

1. `PROJECT_STATUS.md`
2. `base/MASTER_PROFILE.md`
3. `base/NON_NEGOTIABLE_RULES.md`
4. `base/APPLICATION_MODEL.md`
5. `base/BASE_STRATEGY_QUESTIONS.md`
6. `base/REQUEST_ROUTING.md`
7. `base/QUESTION_STRATEGY_RULES.md`
8. `base/WRITING_RULES.md`
9. `base/STORY_BANK.md`
10. `base/ROLE_FIT_CHECKLIST.md`
11. `base/AGENT_WORKFLOW.md`

지원 회사 폴더가 있으면 추가로:

12. `applications/<회사>/SOURCES.md`
13. `applications/<회사>/DECISION_MEMO.md`
14. `applications/<회사>/JD_NOTES.md`
15. `applications/<회사>/STRATEGY.md`
16. `applications/<회사>/TARGET_COMPANY.md`
17. `applications/<회사>/REVISION_REQUEST.md`
18. `applications/<회사>/QUESTION_MAP.md`
19. `applications/<회사>/writer_pack/05_ACTIVE_DRAFT.txt`

## 해야 할 일

1. 비어 있거나 약한 파일이 무엇인지 본다.
2. 현재 작업에서 먼저 필요한 역할을 고른다.
   - Request Router
   - Source Collector
   - Signal Analyst
   - Strategy Designer
   - Question Planner
   - Draft Writer
   - Compliance Reviewer
3. 새로 써야 할지 기존 초안을 수정해야 할지 판단한다.
4. 사용할 story 후보를 2~3개 고른다.
5. 수정 요청이면 먼저 `REVISION_REQUEST.md`와 `REQUEST_ROUTING.md` 기준으로 분류한다.
6. `SOURCES.md`, `STRATEGY.md`, `QUESTION_MAP.md` 중 비어 있는 파일이 있으면 그 파일부터 채우도록 안내한다.
7. `BASE_STRATEGY_QUESTIONS.md`에서 요구하는 질문이 비어 있으면 source 또는 signal 단계로 되돌린다.

## 출력 형식

```text
작업 유형: 초안 수정
다음 역할:
- Request Router
- Compliance Reviewer

먼저 읽을 파일:
- PROJECT_STATUS.md
- base/MASTER_PROFILE.md
- base/NON_NEGOTIABLE_RULES.md
- base/APPLICATION_MODEL.md
- base/BASE_STRATEGY_QUESTIONS.md
- base/REQUEST_ROUTING.md
- base/QUESTION_STRATEGY_RULES.md
- base/STORY_BANK.md
- applications/<회사>/SOURCES.md
- applications/<회사>/DECISION_MEMO.md
- applications/<회사>/STRATEGY.md
- applications/<회사>/TARGET_COMPANY.md
- applications/<회사>/REVISION_REQUEST.md
- applications/<회사>/QUESTION_MAP.md
- applications/<회사>/writer_pack/05_ACTIVE_DRAFT.txt

판단 메모:
- 실제 업무:
- 수익구조:
- AI 이후 유지되는 부분:
- 차별화 포인트:
- 주력 사업 / 방식:
- 왜 이 회사의 이 직무인가:

전략 메모:
- 한 줄 전략:
- 번역할 경험:
- 빼야 할 인상:

사용할 사례:
- Story 01
- Story 03

주의:
- 없는 사실 추가 금지
- 기존 초안 무시하고 처음부터 다시 쓰지 말 것
- 수정 요청이면 먼저 라우팅부터 할 것
- `SOURCES.md`, `STRATEGY.md`, `QUESTION_MAP.md` 없이 바로 초안 쓰지 말 것
```
