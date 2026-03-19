# REQUEST ROUTING

이 문서는 사용자의 요청이 들어왔을 때 어떤 레이어를 먼저 수정해야 하는지 판단하는 기준이다.

핵심 원칙은 하나다.

`요청이 건드리는 가장 상위 레이어부터 다시 시작하고, 그 아래 단계는 다시 통과시킨다.`

## 라우터의 역할

- 라우터는 별도 writing agent가 아니다.
- 라우터는 요청을 분류하고 실행 순서를 정하는 coordinator다.
- 요청이 단순한지 복합적인지 먼저 판단한다.
- 애매하면 더 상위 레이어로 올려서 처리한다.

## 레이어 구조

### 레이어 0. 전역 규칙

- 파일:
  - `base/NON_NEGOTIABLE_RULES.md`
  - `base/WRITING_RULES.md`
- 예:
  - 쉼표를 줄여라
  - 파일명이나 내부 명칭을 쓰지 마라
  - 더 담백하게 써라

### 레이어 1. 소스 / 시그널

- 파일:
  - `applications/<회사>/SOURCES.md`
  - `applications/<회사>/DECISION_MEMO.md`
  - `applications/<회사>/JD_NOTES.md`
- 예:
  - 최근 시그널을 반영해라
  - 공식 근거를 다시 정리해라
  - 이 직무의 실제 업무를 다시 해석해라

### 레이어 2. 전략 / fit

- 파일:
  - `applications/<회사>/STRATEGY.md`
  - `applications/<회사>/TARGET_COMPANY.md`
- 예:
  - 분석형보다 실행형으로 가자
  - 이번 회사에는 고객 설명 능력보다 운영관리 역량을 전면에 두자
  - 왜 이 회사인지가 약하니 포지셔닝을 다시 잡아라

### 레이어 3. 문항 설계

- 파일:
  - `applications/<회사>/QUESTION_MAP.md`
- 예:
  - 2번과 3번 문항이 겹친다
  - 같은 경험을 쓰되 다른 장면으로 나눠라
  - 지원동기 문항은 회사 이해를 더 앞에 둬라

### 레이어 4. 초안 문장

- 파일:
  - `applications/<회사>/writer_pack/05_ACTIVE_DRAFT.txt`
- 예:
  - 1번 문항을 더 짧게 줄여라
  - 3번 문항 표현을 더 자연스럽게 바꿔라
  - 마지막 문장을 덜 과하게 만들어라

### 레이어 5. 검토 / 수정 우선순위

- 파일:
  - `applications/<회사>/REVISION_LOG.md`
- 예:
  - 어디가 가장 치명적인지 먼저 골라라
  - 이번 수정의 이유를 기록해라

## 기본 라우팅 규칙

### 문장 수정 요청

- 실행 체인:
  - `Draft Writer -> Compliance Reviewer`

### 문항 수정 요청

- 실행 체인:
  - `Question Planner -> Draft Writer -> Compliance Reviewer`

### 전략 수정 요청

- 실행 체인:
  - `Strategy Designer -> Question Planner -> Draft Writer -> Compliance Reviewer`

### 시그널 수정 요청

- 실행 체인:
  - `Source Collector -> Signal Analyst -> Strategy Designer -> Question Planner -> Draft Writer -> Compliance Reviewer`

## 복합 요청 판단법

아래처럼 섞여 있으면 하나로 보지 말고 분해한다.

- "지원동기는 더 담백하게 쓰되, 이번 회사에서는 실행형으로 읽히게 하고, 2번과 3번 중복도 없애라"

이 경우:

1. 전략 수정 있음
2. 문항 수정 있음
3. 문장 수정 있음

따라서 실행 체인은 아래다.

- `Strategy Designer -> Question Planner -> Draft Writer -> Compliance Reviewer`

## 애매할 때 규칙

- 요청이 전략 수정인지 문장 수정인지 애매하면 전략 수정으로 본다.
- 요청이 문항 수정인지 초안 수정인지 애매하면 문항 수정으로 본다.
- 요청이 최신 정보 반영을 요구하면 반드시 시그널 레이어부터 본다.

## 라우터 출력 형식

```text
요청 요약:
- 

요청 유형:
- 문장 수정 / 문항 수정 / 전략 수정 / 시그널 수정 / 복합 요청

가장 상위 영향 레이어:
- 

필수 선행 파일:
- 

실행 체인:
1.
2.
3.

수정 후 반드시 다시 볼 파일:
- 
```
