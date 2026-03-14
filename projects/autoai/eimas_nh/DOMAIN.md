# EIMAS_NH Domain

Last Updated: 2026-03-14

## North Star

EIMAS_NH는 `금리와 채권 시장 이벤트를 확률과 리스크 언어로 구조화해 NH rates/FICC desk가 바로 읽을 수 있는 내부 메모 코파일럿`이다.

기본 산출물은 투자 추천이 아니라 `NHTradingDeskMemoV0`다.

## Ubiquitous Language

| Term | Meaning |
|------|---------|
| `EIMASResult` | 전체 파이프라인 결과물. 크고 범용적이지만 기본 사용자 산출물은 아님 |
| `NHTradingDeskMemoV0` | NH Trading의 rates/FICC 지원용 얇은 desk memo view |
| `desk_view` | 이벤트, 금리, 커브, 시나리오 watchlist를 담는 블록 |
| `execution_risk` | approval, failsafe, 상품/집행 리스크를 담는 블록 |
| `handoff` | 사람이 다시 확인하거나 승인해야 하는 상태 |
| `profile` | 기본 실행 경계를 고정하는 런타임 정책 |
| `nh-trading-v1` | Trading 해석에 필요한 경로만 남기고 trade plan은 끄는 NH용 profile |

## Boundaries

```text
main.py
  -> pipeline/app/profiles.py
  -> pipeline phases
  -> pipeline/schemas.py (full artifact)
  -> pipeline/nh_memo_view.py (thin artifact)
  -> pipeline/role_profiles.py (job-family lens)
```

- `pipeline/schemas.py`는 전체 결과 저장용이다.
- `pipeline/nh_memo_view.py`는 NH Trading 지원용 얇은 계약이다.
- `pipeline/role_profiles.py`는 코어를 바꾸지 않고 직무군별 해석만 바꾸는 층이다.
- `pipeline/app/profiles.py`는 무엇을 기본 경로에서 허용할지 결정한다.
- `tests/test_nh_trading_*.py`는 NH Trading 경계를 잠근다.

## Executable Constraints

- trade plan 노출 여부는 문서가 아니라 `PipelineProfile`에서 제어한다.
- 메모 구조는 설명 문서가 아니라 `NHTradingDeskMemoV0`와 테스트로 고정한다.
- guardrails는 `approval_status`, `failsafe_status`, `audit_metadata`로 표현한다.

## Non-Goals for Default Path

- 범용 투자 추천기
- 자동매매 실행
- 크립토 실시간 전략
- 멀티에이전트 데모 자체를 전면에 내세우는 구조
- IT 직무용 시스템 운영 포트폴리오

## Target Roles

- NH투자증권 Trading
- 증권사 세일즈/운용/지원과 맞닿은 Trading desk
