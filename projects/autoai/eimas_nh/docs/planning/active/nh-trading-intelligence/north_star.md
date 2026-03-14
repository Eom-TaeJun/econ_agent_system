---
plan_id: nh-trading-intelligence
status: active
last_updated: 2026-03-14
---

# NH Trading Intelligence North Star

## Objective

2026년 상반기 NH투자증권 `Trading` 지원에 바로 쓰는 포트폴리오 프로젝트로,
`금리와 채권 시장 이벤트를 확률과 리스크 언어로 구조화해 NH rates/FICC desk용 내부 메모로 만드는 코파일럿`을 만든다.

## Primary Artifact

- `NHTradingDeskMemoV0`
- 기본 실행: `python main.py --full --profile nh-trading-v1`

## Target Role

- NH투자증권 Trading

## Core Message

자기소개서와 면접에서 일관되게 보여야 하는 핵심 메시지는
[`core_message.md`](./core_message.md)에 고정한다.

## Product Story

1. `forecast`에서 금리 기대와 과신 문제를 검증했다.
2. 그 문제를 NH Trading의 `채권/금리/FICC` desk가 읽을 수 있는 메모 문제로 번역한다.
3. 시스템은 이벤트, 금리 레벨/커브, 유동성, 실행 리스크, handoff를 담은 얇은 메모를 만든다.

## Recent Company Signals

2025년 하반기 이후 공개 자료 기준으로 이 프로젝트가 맞춰야 할 NH 신호는 아래다.

- `2025-11-18`: `NH RESEARCH FORUM`에서 채권을 포함한 FICC 및 대체투자 자산 전망과 대응 전략을 전면에 둠
- `2025-12-26`: NH가 2026년 상반기 `채권·CP 최종호가수익률 보고회사`로 유지됨
- `2026-01 ~ 2026-02`: 강승원, 전병하가 금통위, BOJ, 외국인 선물 흐름, 시장 센티, 금리 저평가를 공개적으로 해석
- `2026-01-26`: 국고채 특판 상품을 통해 채권 시장 관점을 실제 고객용 상품 언어로 번역

따라서 메모는 단순 요약보다 아래를 보여줘야 한다.

- 정책/이벤트가 커브와 유동성에 어떻게 연결되는가
- NH가 실제로 보는 채권 가격발견과 시장 센티 언어를 이해하는가
- 그 판단을 desk와 고객이 읽을 수 있는 짧은 메모로 바꿀 수 있는가

## Non-Goals

- 자동매매
- 범용 투자 추천기
- 크립토 중심 데모
- 화려한 멀티에이전트 연출
- IT 직무용 시스템 운영 포트폴리오
- 디지털/서비스기획형 데이터 분석 포트폴리오

## Executable Constraints

- 기본 경계는 `pipeline/app/profiles.py`의 `nh-trading-v1`가 결정한다.
- NH용 얇은 산출물은 `pipeline/nh_memo_view.py`가 결정한다.
- 사람상 번역은 `pipeline/role_profiles.py`의 `securities-trading`이 결정한다.
- 검증은 `tests/test_nh_trading_*.py`가 결정한다.

## Delivery Window

- `2026-03-15`: NH 전용 profile, memo, planning harness 고정
- `2026-03-17`: NH FICC/채권시장동향 기반 `rates memo` 구조 정리
- `2026-03-20`: 자소서와 면접에 직접 쓰는 설명 문장 연결
