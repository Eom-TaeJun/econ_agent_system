---
plan_id: nh-trading-intelligence
status: active
owner: tj
created: 2026-03-14
last_updated: 2026-03-14
related_docs:
  - DOMAIN.md
  - docs/planning/active/nh-trading-intelligence/core_message.md
  - docs/planning/active/nh-trading-intelligence/evaluation_rubric.md
  - docs/planning/active/nh-trading-intelligence/memo_contract.md
  - docs/planning/active/nh-trading-intelligence/north_star.md
  - docs/planning/active/nh-trading-intelligence/sample_scenario_01.md
  - docs/planning/active/nh-trading-intelligence/todo.md
  - docs/planning/active/nh-trading-intelligence/research_notes.md
---

# NH Trading Intelligence Plan

## Goal

`forecast`의 확률/과신 문제와 `EIMAS`의 구조화 능력을
NH투자증권 Trading 지원용 `rates/FICC desk memo copilot`으로 번역한다.

기본 산출물은 `NHTradingDeskMemoV0`다.

## Candidate Story

이 프로젝트를 통해 보여줄 사람상:

**금리와 시장 이벤트를 확률과 리스크의 문제로 해석하고, 그 판단 근거를 Trading desk가 바로 읽을 수 있는 메모로 구조화하는 사람**
**금리와 채권 시장 이벤트를 해석하고, 그 판단 근거를 통계와 데이터로 검증해 NH rates/FICC desk가 읽을 수 있는 메모로 구조화하는 사람**

## Scope

- `nh-trading-v1` 기본 경계 고정
- `EIMASResult -> NHTradingDeskMemoV0` 얇은 산출물 추가
- 금리, 커브, 이벤트, 유동성, 실행 리스크를 메모 코어로 연결
- `forecast`와 자소서용 포지셔닝이 바로 이어지는 설명 계층 유지

## Out of Scope

- 포지션 자동 실행
- 수익률 검증 데모
- 범용 시장 예측 엔진 고도화
- 크립토 특화 리서치
- 장문의 투자 의견서

## Deliverables

1. NH Trading 전용 실행 profile
2. NH Trading desk memo 스키마와 샘플 산출물 틀
3. 사람상과 프로젝트를 잇는 핵심 메시지 문서
4. NH용 README / DOMAIN / CLAUDE 정렬
5. 최소 테스트와 후속 TODO

## Workstreams

### 1. Runtime Gating

- `profiles.py`에 `nh-trading-v1` 추가
- portfolio/trade-plan 노출은 기본 경로에서 차단
- market structure analytics는 기본 경로에 남긴다
- rates/FICC 해석이 약해지는 범용 설명은 문서 상단에서 제거한다

### 2. Thin NH Artifact

- `nh_memo_view.py`를 추가해 NH Trading용 얇은 view를 정의
- 저장 시 full artifact 위에 NH memo를 같이 붙인다
- artifact 이름은 `NHTradingDeskMemoV0`로 고정한다

### 3. Candidate Packaging

- `core_message.md`를 사람상 단일 소스로 유지
- `role_profiles.py`에 `securities-trading` 프로필 추가
- README/DOMAIN에서 NH용 설명을 우선 노출한다

### 4. Research-to-Project Link

- NH 조사 메모와 프로젝트 출력 포인트를 연결한다
- `forecast -> NH memo` 번역 문장을 고정한다
- 이후 sample memo는 `미국 금리 경로 -> 국내 금리커브/FICC` 관점에서 먼저 고정한다

## Success Criteria

- `core_message.md` 한 줄로 프로젝트 목적을 설명할 수 있다
- `python main.py --full --profile nh-trading-v1` 경로가 문서와 코드에서 일치한다
- `NHTradingDeskMemoV0`가 저장 결과에 붙는다
- 새 테스트가 NH 전용 경계를 확인한다
- 문서 첫 화면이 더 이상 MPI가 아니라 NH Trading을 가리킨다

## Risks

- 기존 범용 투자/크립토 경로가 README나 샘플 설명에서 다시 전면에 나올 수 있음
- NH memo가 아직 정적 view 수준이라 desk-specific fields가 부족할 수 있음
- 프로젝트가 Trading보다 IT 포트폴리오처럼 읽힐 위험이 남아 있음
