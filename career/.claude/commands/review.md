---
description: "초안을 규칙과 전략 기준으로 점검한다."
allowed-tools: ["Read", "Glob", "Grep"]
---

# /review — Compliance Reviewer

## 목적

`writer_pack/05_ACTIVE_DRAFT.txt`를 규칙, 전략 반영, fit, 문항 분리 기준으로 검토한다.

## 읽을 파일

1. `base/NON_NEGOTIABLE_RULES.md`
2. `base/ROLE_FIT_CHECKLIST.md`
3. `applications/<회사>/STRATEGY.md`
4. `applications/<회사>/QUESTION_MAP.md`
5. `applications/<회사>/writer_pack/05_ACTIVE_DRAFT.txt`
6. `applications/<회사>/REVISION_LOG.md`

## 해야 할 일

### 1단계: 규칙 위반 점검
- 쉼표 남용 여부
- 내부 명칭과 파일명 노출 여부
- 문항 간 경험과 결론 중복

### 2단계: 전략 반영 검증 (필수)
STRATEGY.md를 열고 초안과 하나씩 대조한다.

- [ ] STRATEGY.md의 회사/직무 언어가 초안에 등장하는가 (구체적으로 어떤 용어가 빠졌는지 적는다)
- [ ] 경험별 번역 지침대로 표현이 바뀌었는가 (원래 서사가 남아 있으면 지적한다)
- [ ] 피할 방향에 해당하는 문장이 없는가 (해당 문장을 인용한다)
- [ ] 보조 역량이 전면 역량보다 부각되지 않았는가 (분량 비교)
- [ ] STRATEGY.md "최종 메시지"와 초안 전체 인상이 일치하는가

### 3단계: 수정 우선순위

## 출력 형식

```text
역할: Compliance Reviewer

규칙 위반:
- 쉼표 남용:
- 내부 명칭 노출:
- 문항 중복:

전략 반영 검증:
- 회사 언어 반영: O/X → 빠진 용어: [...]
- 번역 지침 반영: O/X → 미반영 경험: [...]
- 피할 방향 위반: O/X → 해당 문장: [...]
- 역량 비중 적절: O/X → 보조 역량 부각 지점: [...]
- 최종 메시지 일치: O/X

수정 우선순위:
1. (전략 미반영이 있으면 항상 최우선)
2.
3.
```
