# AGENT WORKFLOW

이 문서는 자기소개서 작업을 함수처럼 고정된 단계로 나누고 각 단계를 에이전트처럼 역할 분담하기 위한 기준 문서다.

핵심은 `SOURCES -> DECISION/JD -> STRATEGY/TARGET -> QUESTION_MAP -> DRAFT -> REVIEW` 흐름을 깨지 않는 것이다.

복잡한 요청이 들어오면 먼저 `REQUEST_ROUTING.md` 기준으로 라우팅한 뒤 역할 체인을 시작한다.

## 함수와 에이전트

- 함수는 반복되는 작업 단계다.
- 에이전트는 그 단계를 맡는 역할이다.
- 각 역할은 입력 파일과 출력 파일이 명확해야 한다.
- 앞 단계 산출물이 비어 있으면 다음 단계로 넘어가지 않는다.
- 라우터는 별도 writing agent가 아니라 요청을 분류하는 coordinator다.

## Step 0. Request Router

- 목적: 사용자의 요청이 어느 레이어를 건드리는지 먼저 판단한다.
- 기준 파일:
  - `base/REQUEST_ROUTING.md`
  - `applications/<회사>/REVISION_REQUEST.md`
- 원칙:
  - 요청이 건드리는 가장 상위 레이어부터 다시 시작한다.
  - 애매하면 더 상위 레이어로 올린다.
  - 요청이 복합적이면 체인을 분해하지 말고 상위 레이어부터 아래까지 다시 통과시킨다.

## 역할 1. Source Collector

- 목적: 다채널로 소스를 수집하고 SOURCES.md를 채운다.
- 도구: WebSearch, WebFetch
- 입력:
  - `base/BASE_STRATEGY_QUESTIONS.md`
  - 공고 링크
  - 회사 홈페이지
- 수집 채널 (6단계):
  1. 공식 채널: 채용 공고, 회사 사이트, IR/공시/재무
  2. 현업 인터뷰: 공식 채용 페이지 인터뷰 + 외부(유튜브/블로그/기사/팟캐스트)
  3. 직무 발행 리포트: 해당 부서가 발행한 리포트, 코멘터리, 전략 노트
  4. 업계 뉴스 / 대외 인정: 최근 6개월 기사, 수상/선정
  5. 경쟁사 비교: 같은 업권 2~3곳 대비 차별점
  6. 커뮤니티 / 후기: 면접 후기, 직무 후기 (신뢰도 표시 필수)
- 출력:
  - `applications/<회사>/SOURCES.md`
- 완료 조건:
  - SOURCES.md 상단 수집 상태 표에서 빈 칸이 3개 미만이어야 한다.
  - 현업 인터뷰가 최소 1개 이상 확보돼 있어야 한다.
  - 직무 발행 리포트가 최소 1개 이상 확인돼 있어야 한다 (없으면 "해당 없음 확인" 표시).
  - 최근 6개월 내 시그널이 최소 2개 이상 있어야 한다.
  - 공식 소스와 외부 정보가 충돌하면 해석 메모로 남아 있어야 한다.

## 역할 2. Signal Analyst

- 목적: 회사 시그널과 직무의 실제 문제를 정리한다.
- 입력:
  - `base/APPLICATION_MODEL.md`
  - `base/BASE_STRATEGY_QUESTIONS.md`
  - `applications/<회사>/SOURCES.md`
  - `applications/<회사>/DECISION_MEMO.md`
  - `applications/<회사>/JD_NOTES.md`
- 출력:
  - `DECISION_MEMO.md`
  - `JD_NOTES.md`
- 완료 조건:
  - 회사가 중요하게 보는 문제
  - 다른 회사와 구분되는 차별점
  - 주력 사업, 자산군, 방식
  - 실제 업무
  - 실제 업무 언어와 지표
  - 수익구조
  - AI 이후 남는 부분
  - 평가 포인트가 정리돼 있어야 한다.

## 역할 3. Strategy Designer

- 목적: 회사 문제와 내 경험을 연결하는 한 줄 전략을 만든다.
- 입력:
  - `base/MASTER_PROFILE.md`
  - `base/STORY_BANK.md`
  - `base/BASE_STRATEGY_QUESTIONS.md`
  - `base/NON_NEGOTIABLE_RULES.md`
  - `applications/<회사>/DECISION_MEMO.md`
  - `applications/<회사>/JD_NOTES.md`
  - `applications/<회사>/STRATEGY.md`
  - `applications/<회사>/TARGET_COMPANY.md`
- 출력:
  - `STRATEGY.md`
  - `TARGET_COMPANY.md`
- 완료 조건:
  - 한 줄 전략
  - 직무 해석
  - 왜 이 회사의 이 직무인지에 대한 구체 문장
  - 경험 번역 기준
  - 피해야 할 방향
  - 강조할 역량이 정리돼 있어야 한다.

## 역할 4. Question Planner

- 목적: 문항별 역할과 사례 배정을 정해 중복을 막는다.
- 입력:
  - `base/QUESTION_STRATEGY_RULES.md`
  - `applications/<회사>/STRATEGY.md`
  - `applications/<회사>/TARGET_COMPANY.md`
  - `applications/<회사>/QUESTION_MAP.md`
- 출력:
  - `QUESTION_MAP.md`
- 완료 조건:
  - 각 문항이 증명할 한 가지
  - 문항별 주력 사례
  - 다른 문항과 겹치면 안 되는 점
  - 내부 용어를 바꿔 쓸 업무 언어가 적혀 있어야 한다.

## 역할 5. Draft Writer

- 목적: 전략과 문항 설계를 실제 문장으로 바꾼다.
- 입력:
  - `base/NON_NEGOTIABLE_RULES.md`
  - `base/WRITING_RULES.md`
  - `applications/<회사>/STRATEGY.md`
  - `applications/<회사>/QUESTION_MAP.md`
  - `applications/<회사>/writer_pack/05_ACTIVE_DRAFT.txt`
- 작업 순서:
  1. `STRATEGY.md`를 먼저 읽고 회사 언어, 경험 번역 지침, 피할 방향을 확인한다.
  2. `QUESTION_MAP.md` 하단의 "전략 → 초안 전달 체크리스트"를 확인한다.
  3. 문항별 초안을 쓴다.
  4. 초안 완료 후 체크리스트 항목을 하나씩 대조한다.
- 출력:
  - `writer_pack/05_ACTIVE_DRAFT.txt`
- 완료 조건:
  - 문항별 의도와 초안이 일치해야 한다.
  - 파일명과 내부 명칭이 제거돼 있어야 한다.
  - 문항 간 중복이 없어야 한다.
  - STRATEGY.md의 회사 언어가 초안에 최소 1회 이상 등장해야 한다.
  - 경험별 번역 지침대로 표현이 바뀌어 있어야 한다.
  - 피할 방향에 해당하는 문장이 없어야 한다.
  - 보조 역량이 전면 역량보다 부각되지 않아야 한다.

## 역할 6. Compliance Reviewer

- 목적: 규칙 위반과 전략 누락을 검토한다.
- 입력:
  - `base/NON_NEGOTIABLE_RULES.md`
  - `base/ROLE_FIT_CHECKLIST.md`
  - `applications/<회사>/STRATEGY.md`
  - `applications/<회사>/QUESTION_MAP.md`
  - `applications/<회사>/writer_pack/05_ACTIVE_DRAFT.txt`
  - `applications/<회사>/REVISION_LOG.md`
- 출력:
  - 수정 우선순위
  - `REVISION_LOG.md`
- 완료 조건:
  - 쉼표 남용 여부
  - 내부 명칭 노출 여부
  - 문항 중복 여부
  - 전략 반영 검증 (아래 4개 항목 필수):
    - STRATEGY.md의 회사 언어가 초안에 등장하는가
    - 경험별 번역 지침이 초안에 반영됐는가
    - 피할 방향에 해당하는 문장이 없는가
    - 보조 역량이 전면 역량보다 부각되지 않았는가

## 멈춤 조건

- `SOURCES.md`가 비어 있으면 시그널 해석 금지
- `DECISION_MEMO.md`와 `JD_NOTES.md`가 약하면 전략 수립 금지
- `STRATEGY.md`가 약하면 문항 배치 금지
- `QUESTION_MAP.md`가 비어 있으면 초안 작성 금지
- 규칙 위반이 많으면 새 초안보다 기존 초안 수정이 우선이다
- 복합 요청인데 라우팅 판단이 없으면 초안 수정 금지
