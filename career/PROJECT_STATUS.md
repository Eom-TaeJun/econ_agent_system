# PROJECT STATUS

기준일: 2026-03-20

이 문서는 다른 AI가 현재 `career/` 작업공간 상태를 빠르게 파악하고 이어서 작업하기 위한 인수인계 문서다.

## 현재까지 완료한 일

- `career/`를 실제 작업 공간으로 정리했다.
- `/home/tj/projects/자기소개서`는 조사 메모와 과거 산출물 보관소로 분리하기로 했다.
- 전역 규칙 파일을 만들었다.
  - `base/NON_NEGOTIABLE_RULES.md`
  - `base/QUESTION_STRATEGY_RULES.md`
  - `base/AGENT_WORKFLOW.md`
- 전역 조사 질문 파일을 만들었다.
  - `base/BASE_STRATEGY_QUESTIONS.md`
- 회사별 템플릿을 확장했다.
  - `SOURCES.md`
  - `STRATEGY.md`
  - `REVISION_REQUEST.md`
  - `QUESTION_MAP.md`
  - `writer_pack/05_ACTIVE_DRAFT.txt`
- 역할별 명령 문서를 만들었다.
  - `.claude/commands/apply.md`
  - `.claude/commands/route.md`
  - `.claude/commands/source.md`
  - `.claude/commands/signal.md`
  - `.claude/commands/strategy.md`
  - `.claude/commands/question.md`
  - `.claude/commands/draft.md`
  - `.claude/commands/review.md`

## 왜 이렇게 바꿨는가

기존 문제는 아래 4가지였다.

1. 미리 정한 전략이 초안과 수정 과정에서 약해졌다.
2. 시그널과 공식 소스를 수집해도 fit 문장으로 번역되지 않고 나열로 끝나는 경우가 있었다.
3. 여러 문항에서 같은 경험의 같은 장면과 같은 결론이 반복됐다.
4. 복잡한 수정 요청이 들어오면 어느 단계부터 다시 봐야 하는지 기준이 약했다.

따라서 지금 구조는 아래 흐름을 강제한다.

`SOURCES -> DECISION/JD -> STRATEGY/TARGET -> QUESTION_MAP -> DRAFT -> REVIEW`

그리고 모든 회사 조사 전에 아래 질문을 강제한다.

- 최근 2025년 하반기 이후와 현재 연도 시그널은 무엇인가
- 다른 회사와 구분되는 차별점은 무엇인가
- 주력 사업, 자산군, 운영 방식은 무엇인가
- 직무가 실제로 쓰는 언어와 지표는 무엇인가
- 왜 이 회사의 이 직무인가

## 핵심 결정 사항

- 상황마다 새 agent를 늘리는 방식은 쓰지 않는다.
- 고정 역할 agent와 request router를 같이 쓰는 방식으로 간다.
- 요청이 여러 레이어를 건드리면 가장 상위 레이어부터 다시 시작한다.
- 문장 수정 전에 전략과 문항 설계가 이미 맞는지 먼저 확인한다.
- `QUESTION_MAP.md` 없이 곧바로 초안을 만들지 않는다.

## 현재 파일 역할

- `career/base/`
  - 변하지 않는 규칙과 작업 원칙
- `career/applications/<회사>/`
  - 해당 회사에만 적용되는 소스, 전략, 문항 설계, 초안
- `/home/tj/projects/자기소개서`
  - 과거 전략 메모, 최근 시그널 정리, 포지셔닝 문서, 임시 산출물

## 현재 운영 방식

1. `/apply`로 현재 상태와 선행 파일 부족 여부를 본다.
2. 수정 요청이면 `/route`로 먼저 라우팅한다.
3. 자료가 없으면 `Source Collector`부터 시작한다.
4. `BASE_STRATEGY_QUESTIONS.md` 기준으로 빠진 조사 질문이 있으면 다시 source 단계로 올린다.
5. 시그널 해석이 약하면 `Signal Analyst`를 먼저 돌린다.
6. 포지셔닝이 약하면 `Strategy Designer`를 먼저 돌린다.
7. 문항이 겹치면 `Question Planner`를 먼저 돌린다.
8. 그 뒤에만 `Draft Writer`가 초안을 쓴다.
9. 마지막은 항상 `Compliance Reviewer`가 맡는다.

## 복잡한 요청 처리 원칙

- 문장 수정 요청:
  - `Draft Writer -> Compliance Reviewer`
- 문항 역할 수정 요청:
  - `Question Planner -> Draft Writer -> Compliance Reviewer`
- 전략 수정 요청:
  - `Strategy Designer -> Question Planner -> Draft Writer -> Compliance Reviewer`
- 시그널이나 최신 자료 반영 요청:
  - `Source Collector -> Signal Analyst -> Strategy Designer -> Question Planner -> Draft Writer -> Compliance Reviewer`
- 복합 요청:
  - 가장 상위 영향 레이어를 먼저 잡고 그 아래 체인을 모두 다시 통과시킨다.

## 현재 남은 작업

- 기존 회사 폴더를 새 템플릿 구조에 맞게 천천히 이관해야 한다.
- 특히 기존 `kistemp-group` 폴더는 `QUESTION_MAP.md`와 `REVISION_REQUEST.md` 기준으로 다시 맞출 필요가 있다.
- 실제 지원 회사 하나를 골라 `SOURCES -> STRATEGY -> QUESTION_MAP -> DRAFT` 순서로 첫 완주 사례를 만들어야 한다.
- 사용자의 새 요청이 들어오면 `REVISION_REQUEST.md`에 분류 기록을 먼저 남기는 습관을 정착시켜야 한다.
- `BASE_STRATEGY_QUESTIONS.md` 기준으로 다른 회사도 같은 조사 깊이로 수집되게 해야 한다.

## 현재 활성 작업

- 회사:
  - `applications/nh-investment-securities-2026-h1`
- 상태:
  - NH Trading 지원서가 현재 가장 앞선 작업본이다.
  - 공식 공고와 writer_pack은 이미 정리돼 있다.
  - `채용 페이지`, `직무 인터뷰`, `공식 트레이딩 채널`, `IR 비전`, `CEO 메시지`, `2025 사업보고서`, `2025년 4분기 실적보고서`까지 반영됐다.
- 이번 세션에서 저장한 핵심:
  - NH Trading은 일반 증권사 Trading 공통 문장보다 `전망 -> 대응 전략`, `채권/FICC`, `가격발견 신뢰`, `실행 중심 정렬` 축으로 읽어야 한다.
  - 우대역량 `경제, 통계분석, 코딩, 데이터분석, 영어`는 `시장 판단을 더 정교하게 만드는 보조 역량`으로 해석해야 한다.
  - 공식 사업보고서 기준 Trading은 `상품운용`, `파생상품 공급`, `자기자본투자`, `운용전략`, `리스크관리`, `구조화상품` 축으로 읽어야 한다.
  - 공식 실적보고서 기준 NH는 `국고3Y`, `국고10Y`, `크레딧 스프레드`, `전략적 자산배분`, `운용손익` 언어로 Trading과 운용을 설명한다.
  - 다음 세션은 NH 폴더의 `SOURCES.md`, `writer_pack/01_COMPANY_ROLE.md`, `writer_pack/05_ACTIVE_DRAFT.txt`를 먼저 읽고 바로 이어서 작업하면 된다.

## 새 요약 문서

- 전체 구조와 현재 상태를 한 번에 보려면 `PROCESS_SUMMARY.md`를 먼저 읽는다.

## 다음 AI가 먼저 읽을 파일

1. `CLAUDE.md`
2. `PROCESS_SUMMARY.md`
3. `PROJECT_STATUS.md`
4. `base/BASE_STRATEGY_QUESTIONS.md`
5. `base/NON_NEGOTIABLE_RULES.md`
6. `base/REQUEST_ROUTING.md`
7. `base/AGENT_WORKFLOW.md`
8. 작업 중인 회사 폴더의 `SOURCES.md`, `STRATEGY.md`, `QUESTION_MAP.md`, `writer_pack/01_COMPANY_ROLE.md`, `writer_pack/05_ACTIVE_DRAFT.txt`

## 주의

- 명령 문서들은 실행 프로그램이 아니라 역할 지시서다.
- 현재 구조는 설계와 템플릿 정비까지 진행된 상태다.
- 실제 회사별 데이터 이관은 아직 전부 끝난 상태가 아니다.
