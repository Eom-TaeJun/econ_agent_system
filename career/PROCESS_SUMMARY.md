# PROCESS SUMMARY

기준일: 2026-03-20

이 문서는 `career/` 작업공간의 현재 구조, 작업 프로세스, 필수 조사 질문, NH 현재 상태를 한 번에 요약한 문서다.

## 1. 이 작업공간의 목적

- 자기소개서를 세션 기억이 아니라 파일 기반으로 관리한다.
- `내 사실`, `내 사례`, `회사별 조사`, `회사별 전략`, `회사별 초안`을 분리한다.
- 다른 AI가 와도 같은 파일 순서와 같은 질문으로 이어서 작업할 수 있게 한다.

## 2. 현재 작업 구조

- 전역 기준:
  - `base/MASTER_PROFILE.md`
  - `base/STORY_BANK.md`
  - `base/NON_NEGOTIABLE_RULES.md`
  - `base/APPLICATION_MODEL.md`
  - `base/BASE_STRATEGY_QUESTIONS.md`
  - `base/AGENT_WORKFLOW.md`
  - `base/REQUEST_ROUTING.md`
  - `base/QUESTION_STRATEGY_RULES.md`
  - `base/ROLE_FIT_CHECKLIST.md`
- 회사별 작업:
  - `applications/<회사>/SOURCES.md`
  - `applications/<회사>/DECISION_MEMO.md`
  - `applications/<회사>/JD_NOTES.md`
  - `applications/<회사>/STRATEGY.md`
  - `applications/<회사>/TARGET_COMPANY.md`
  - `applications/<회사>/REVISION_REQUEST.md`
  - `applications/<회사>/QUESTION_MAP.md`
  - `applications/<회사>/REVISION_LOG.md`
  - `applications/<회사>/writer_pack/`
- 외부 보관소:
  - `/home/tj/projects/자기소개서`
  - 과거 메모, 조사 자료, 임시 산출물 보관

## 3. 핵심 프로세스

- 기본 흐름:
  - `SOURCES -> DECISION/JD -> STRATEGY/TARGET -> QUESTION_MAP -> DRAFT -> REVIEW`
- 수정 흐름:
  - 문장 수정: `DRAFT -> REVIEW`
  - 문항 수정: `QUESTION_MAP -> DRAFT -> REVIEW`
  - 전략 수정: `STRATEGY -> QUESTION_MAP -> DRAFT -> REVIEW`
  - 시그널 수정: `SOURCES -> DECISION/JD -> STRATEGY -> QUESTION_MAP -> DRAFT -> REVIEW`
- 원칙:
  - 가장 상위 레이어부터 다시 시작한다.
  - 상위 파일이 약하면 하위 단계로 내려가지 않는다.
  - `QUESTION_MAP.md` 없이 바로 초안으로 가지 않는다.
  - 실제 자소서 작업본은 `writer_pack/05_ACTIVE_DRAFT.txt` 하나만 쓴다.

## 4. 현재 고정된 역할

- Source Collector
  - 공식 소스, 외부 참고, 최근 시그널, 충돌 정보를 모은다.
- Signal Analyst
  - 회사 문제, 직무 실제 성격, 수익구조, 차별점, 현업 언어를 해석한다.
- Strategy Designer
  - 회사 문제와 내 경험을 연결하는 한 줄 전략을 만든다.
- Question Planner
  - 문항별 역할, 사례 배정, 중복 금지를 설계한다.
- Draft Writer
  - 설계된 전략과 문항 역할을 실제 문장으로 옮긴다.
- Compliance Reviewer
  - 규칙 위반, 전략 누락, 문항 중복을 점검한다.

## 5. 현재 가장 중요한 전역 규칙

- 전략이 초안보다 우선이다.
- 회사 시그널과 직무 문제를 먼저 적고 그 다음 fit을 쓴다.
- 파일명, 프로젝트명, 내부 명칭을 그대로 쓰지 않는다.
- 같은 경험을 재사용해도 장면과 결론은 질문마다 다르게 쓴다.
- `왜 이 회사인지`와 `왜 내가 맞는지`를 섞지 않는다.
- 쉼표 남용을 피한다.
- 오래된 인상이나 일반론 대신 공식 자료와 최근 시그널을 우선한다.

## 6. 기본전략 질문

모든 회사에서 아래는 반드시 조사한다.

- 공식 채용 공고와 실제 지원 페이지
- 회사 메인, 회사 소개, 비전, 대표 메시지
- IR, 사업보고서, 실적보고서, 설명회 자료
- 직무 인터뷰, 현직자 인터뷰, 공식 리포트 채널
- 2025년 하반기 이후와 현재 연도 시그널
- 다른 회사와 구분되는 차별점
- 주력 산업, 사업, 자산군, 운영 방식
- 직무가 실제로 쓰는 언어, 지표, 리스크
- JD 우대역량의 실제 중요도와 이유
- 왜 같은 업권 다른 회사가 아니라 이 회사의 이 직무인지

## 7. 현재 NH 작업 요약

- 회사:
  - `applications/nh-investment-securities-2026-h1`
- 직무:
  - `Trading`
- 문항:
  - `지원분야에 관련된 경험 등을 바탕으로 자유롭게 작성`
- 현 상태:
  - 공식 채용공고, 직무 인터뷰, 공식 트레이딩 채널, IR 비전, CEO 메시지, 2025 사업보고서, 2025년 4분기 실적보고서까지 반영 완료
- NH Trading을 읽는 현재 결론:
  - 일반적인 증권사 Trading보다 `채권/FICC`, `가격발견`, `운용전략`, `리스크관리`, `세일즈·운용·지원 handoff`가 선명하다.
- NH 차별화 포인트:
  - `채권·CP 최종호가수익률 보고회사`
  - Trading을 `상품운용`, `파생상품 공급`, `자기자본투자`로 정의
  - 실적 설명에 `금리`, `국고3Y`, `국고10Y`, `크레딧 스프레드`, `전략적 자산배분`, `운용손익` 언어 사용
  - 현업 인터뷰에 `아침 회의`, `브로커 호가`, `장외 거래`, `현/선물 레벨`, `세일즈·운용 연결` 등장
- 현재 남은 일:
  - 위 공식 신호를 더 압축해 `왜 NH Trading인가` 문단을 최종 제출형으로 재작성

## 8. 다음 AI가 먼저 읽을 파일

1. `CLAUDE.md`
2. `PROCESS_SUMMARY.md`
3. `PROJECT_STATUS.md`
4. `base/BASE_STRATEGY_QUESTIONS.md`
5. `base/NON_NEGOTIABLE_RULES.md`
6. `base/AGENT_WORKFLOW.md`
7. 작업 중인 회사 폴더의 `SOURCES.md`
8. 작업 중인 회사 폴더의 `STRATEGY.md`
9. 작업 중인 회사 폴더의 `QUESTION_MAP.md`
10. 작업 중인 회사 폴더의 `writer_pack/01_COMPANY_ROLE.md`
11. 작업 중인 회사 폴더의 `writer_pack/05_ACTIVE_DRAFT.txt`

## 9. 지금 시점의 실무적 결론

- 가장 중요한 것은 `초안 잘 쓰기`보다 `조사 질문과 전략 구조를 모든 회사에 공통 적용하는 것`이다.
- NH에서 수집한 방식은 이제 특정 회사 전용이 아니라 전역 기준이 됐다.
- 앞으로 다른 회사를 시작할 때도 같은 질문으로 조사하고 같은 파일 구조로 저장하면 된다.
