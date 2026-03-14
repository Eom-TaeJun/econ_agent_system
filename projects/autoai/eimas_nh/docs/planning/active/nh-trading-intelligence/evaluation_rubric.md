---
plan_id: nh-trading-intelligence
status: active
last_updated: 2026-03-14
---

# NH Trading Evaluation Rubric

목적:
- 이 프로젝트가 NH투자증권 Trading 지원용 포트폴리오로서 충분히 설득력 있는지 판단한다.
- 기능 추가보다 `어떤 사람으로 읽히는지`를 먼저 점검한다.

---

## Pass Question

이 프로젝트를 본 사람이 아래 한 줄로 나를 설명할 수 있어야 한다.

**금리와 채권 시장 이벤트를 해석하고, 그 판단 근거를 통계와 데이터로 검증해 NH Trading의 rates/FICC desk가 읽을 수 있는 메모로 구조화하는 지원자**

이 문장으로 자연스럽게 요약되지 않으면 방향이 흔들린 것이다.

---

## Scoring Criteria

각 항목은 `0~2점`으로 본다.

### 1. Candidate Clarity

질문:
- 이 결과물이 `Trading 지원자`를 보여주는가
- 아니면 `IT 개발 프로젝트`처럼 보이는가

2점:
- 사람상이 바로 읽힌다
- 경제학, forecast, EIMAS가 한 줄로 연결된다

1점:
- Trading과 IT 톤이 섞인다

0점:
- 범용 AI/개발 데모처럼 보인다

### 2. Trading Desk Relevance

질문:
- `채권/금리/FICC` desk 문맥이 선명한가
- 금리 레벨, 커브, 유동성, 이벤트 재가격(repricing) 시사점이 살아 있는가

2점:
- 금리 해석이 FICC 문맥으로 바로 이어진다

1점:
- 시장 코멘트는 있으나 desk 사용 맥락이 약하다

0점:
- 일반 경제 리포트 수준에 머문다

### 3. Risk and Uncertainty Thinking

질문:
- 방향 예측보다 확률, 과신, 손실 가능성, 대안 시나리오를 같이 보이는가

2점:
- base case와 risk case가 같이 보인다
- `어떻게 틀릴 수 있는지`가 명시된다

1점:
- 리스크 언급은 있으나 형식적이다

0점:
- 방향 단정, 수익률 자랑, 강한 확신 위주다

### 4. Execution / Product Risk Awareness

질문:
- 유동성, 증거금, 반대매매, 커브 급변, duration shock 같은 실행 리스크를 이해한 흔적이 있는가

2점:
- 실행/상품 리스크와 human handoff가 같이 보인다

1점:
- 위험고지는 있으나 desk 관점 연결이 약하다

0점:
- 시황만 있고 실행 리스크가 없다

### 5. Evidence and Restraint

질문:
- 근거, 승인, handoff, 검증 가능한 상태를 남기는가
- 과장 없이 설명하는가

2점:
- approval/failsafe/audit가 있고 non-goal이 지켜진다

1점:
- 근거는 있으나 통제 구조가 약하다

0점:
- 자동매매, 과장된 AI, 수익률 위주 설명이 전면에 나온다

---

## Red Flags

아래가 보이면 방향이 틀어진 것으로 본다.

- `자동매매`, `trade plan`, `paper execution`이 NH 기본 데모 전면에 나옴
- `크립토`, `에이전트`, `LLM 스택` 설명이 핵심 메시지를 덮음
- 수익률, 샤프, 백테스트가 먼저 보임
- `왜 NH Trading인가`보다 `무슨 기술을 썼는가`가 더 크게 보임
- 메모가 아니라 범용 대시보드처럼 보임
- 채권/금리보다 데이터분석 자체가 전면에 나옴

---

## Minimum Pass Bar

총점 `8/10` 이상을 통과 기준으로 둔다.

추가 조건:
- `Candidate Clarity` 2점
- `Risk and Uncertainty Thinking` 2점

이 두 항목이 2점이 아니면 전체 점수와 무관하게 재작업한다.
