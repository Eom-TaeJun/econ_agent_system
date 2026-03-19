# Career Workspace

이 폴더는 자기소개서, 이력서, 지원동기, 프로젝트 서술을 **세션 기억에 의존하지 않고 파일 기반으로 관리**하기 위한 작업 공간이다.

핵심 원칙:

- 변하지 않는 사실과 지원서 초안을 분리한다
- 문체 규칙을 별도 파일로 둔다
- 경험 사례를 재사용 가능한 단위로 저장한다
- 회사별 초안은 `applications/` 아래에서 분기한다

## 구조

```text
career/
├── CLAUDE.md
├── README.md
├── PROJECT_STATUS.md
├── base/
│   ├── MASTER_PROFILE.md
│   ├── NON_NEGOTIABLE_RULES.md
│   ├── APPLICATION_MODEL.md
│   ├── BASE_STRATEGY_QUESTIONS.md
│   ├── AGENT_WORKFLOW.md
│   ├── REQUEST_ROUTING.md
│   ├── QUESTION_STRATEGY_RULES.md
│   ├── WRITING_RULES.md
│   ├── STORY_BANK.md
│   └── ROLE_FIT_CHECKLIST.md
├── applications/
│   └── _template/
│       ├── SOURCES.md
│       ├── DECISION_MEMO.md
│       ├── JD_NOTES.md
│       ├── STRATEGY.md
│       ├── TARGET_COMPANY.md
│       ├── REVISION_REQUEST.md
│       ├── QUESTION_MAP.md
│       ├── REVISION_LOG.md
│       └── writer_pack/
│           ├── 00_READ_FIRST.md
│           ├── 01_COMPANY_ROLE.md
│           ├── 02_MY_SOURCE.md
│           ├── 03_MY_INTERPRETATION.md
│           ├── 04_EXAMPLES.md
│           └── 05_ACTIVE_DRAFT.txt
├── references/
└── .claude/
    └── commands/
        ├── apply.md
        ├── route.md
        ├── source.md
        ├── signal.md
        ├── strategy.md
        ├── question.md
        ├── draft.md
        └── review.md
```

## 사용 순서

1. `base/MASTER_PROFILE.md`에 사실을 채운다
2. `base/NON_NEGOTIABLE_RULES.md`에 절대 규칙을 적는다
3. `base/STORY_BANK.md`에 사례를 채운다
4. `base/APPLICATION_MODEL.md`로 조사 흐름을 고정한다
5. `base/BASE_STRATEGY_QUESTIONS.md`로 모든 회사에 공통 적용할 조사 질문을 고정한다
6. `base/AGENT_WORKFLOW.md`로 역할별 입출력을 고정한다
7. `base/REQUEST_ROUTING.md`로 복잡한 요청의 처리 순서를 고정한다
8. `base/QUESTION_STRATEGY_RULES.md`로 문항 분배 기준을 고정한다
9. 지원 회사가 생기면 `applications/_template/`를 복사해 새 폴더를 만든다
10. 출처와 링크는 `SOURCES.md`
11. 회사와 직무 판단은 `DECISION_MEMO.md`
12. JD 분석은 `JD_NOTES.md`
13. 한 줄 전략과 번역 기준은 `STRATEGY.md`
14. 강조 포인트는 `TARGET_COMPANY.md`
15. 수정 요청 분류는 `REVISION_REQUEST.md`
16. 문항별 역할과 사례 분배는 `QUESTION_MAP.md`
17. 실제 자기소개서 초안은 `writer_pack/05_ACTIVE_DRAFT.txt`
18. 수정 이유는 `REVISION_LOG.md`

즉, 자기소개서는 "기억해서 쓰는 작업"이 아니라 **사실 파일 + 사례 파일 + 회사별 판단 메모 + 회사별 초안 파일**을 조합하는 작업으로 바꾼다.

## 권장 역할 분리

- `career/`는 항상 기준 문서와 현재 작업본을 두는 곳이다.
- `/home/tj/projects/자기소개서`는 조사 메모, 과거 산출물, 임시 텍스트를 모아두는 보관소로 쓰는 편이 안전하다.
- 변하지 않는 규칙은 반드시 `career/base/`에 둔다.
- 회사별 전략과 문항별 분배는 반드시 `career/applications/<회사>/`에 둔다.

## 역할 기반 운영

실제 운영은 아래 6개 역할로 나눈다.

1. Source Collector
2. Signal Analyst
3. Strategy Designer
4. Question Planner
5. Draft Writer
6. Compliance Reviewer

각 역할의 입력 파일과 출력 파일은 `base/AGENT_WORKFLOW.md`를 따른다.

복잡한 요청이 들어오면 먼저 `Request Router`가 `base/REQUEST_ROUTING.md` 기준으로 실행 체인을 정한다.
