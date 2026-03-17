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
├── base/
│   ├── MASTER_PROFILE.md
│   ├── APPLICATION_MODEL.md
│   ├── WRITING_RULES.md
│   ├── STORY_BANK.md
│   └── ROLE_FIT_CHECKLIST.md
├── applications/
│   └── _template/
│       ├── DECISION_MEMO.md
│       ├── JD_NOTES.md
│       ├── TARGET_COMPANY.md
│       ├── DRAFT_SELF_INTRO.md
│       └── REVISION_LOG.md
├── references/
└── .claude/
    └── commands/
        └── apply.md
```

## 사용 순서

1. `base/MASTER_PROFILE.md`에 사실을 채운다
2. `base/STORY_BANK.md`에 사례를 채운다
3. `base/APPLICATION_MODEL.md`로 조사 흐름을 고정한다
4. 지원 회사가 생기면 `applications/_template/`를 복사해 새 폴더를 만든다
5. 회사와 직무 판단은 `DECISION_MEMO.md`
6. JD 분석은 `JD_NOTES.md`
7. 강조 포인트는 `TARGET_COMPANY.md`
8. 실제 자기소개서 초안은 `DRAFT_SELF_INTRO.md`
9. 수정 이유는 `REVISION_LOG.md`

즉, 자기소개서는 "기억해서 쓰는 작업"이 아니라 **사실 파일 + 사례 파일 + 회사별 판단 메모 + 회사별 초안 파일**을 조합하는 작업으로 바꾼다.
