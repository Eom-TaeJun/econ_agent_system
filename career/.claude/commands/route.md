---
description: "사용자 요청을 분류해 어떤 역할 체인으로 처리할지 정한다."
allowed-tools: ["Read", "Glob", "Grep"]
---

# /route — Request Router

## 목적

사용자 요청을 `문장 수정`, `문항 수정`, `전략 수정`, `시그널 수정`, `복합 요청` 중 하나로 분류한다.

그 다음 어떤 파일부터 다시 봐야 하는지와 어떤 역할 체인으로 움직일지를 정한다.

## 읽을 파일

1. `PROJECT_STATUS.md`
2. `base/REQUEST_ROUTING.md`
3. `base/NON_NEGOTIABLE_RULES.md`
4. 작업 중인 경우 `applications/<회사>/REVISION_REQUEST.md`
5. 작업 중인 경우 `applications/<회사>/STRATEGY.md`
6. 작업 중인 경우 `applications/<회사>/QUESTION_MAP.md`
7. 작업 중인 경우 `applications/<회사>/DRAFT_SELF_INTRO.md`

## 해야 할 일

1. 요청을 한 줄로 요약한다.
2. 가장 상위 영향 레이어를 고른다.
3. 필요한 실행 체인을 정한다.
4. 먼저 수정해야 할 파일과 마지막에 다시 검토할 파일을 적는다.
5. 가능하면 `REVISION_REQUEST.md`에도 같은 판단을 남긴다.

## 출력 형식

```text
역할: Request Router

요청 요약:
- 

요청 유형:
- 문장 수정 / 문항 수정 / 전략 수정 / 시그널 수정 / 복합 요청

가장 상위 영향 레이어:
- 

실행 체인:
1.
2.
3.

먼저 수정할 파일:
- 

마지막 검토 파일:
- 
```
