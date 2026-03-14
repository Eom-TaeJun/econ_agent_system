# EIMAS_NH Quick Facts

`EIMAS_NH`는 NH투자증권 Trading 지원용으로, 금리와 채권 시장 이벤트를 확률·리스크 언어의 rates/FICC memo로 바꾸는 얇은 코파일럿이다.

용어와 경계는 [`DOMAIN.md`](./DOMAIN.md)에서 본다.

## Read Order

1. `command.md`
2. `docs/planning/active/nh-trading-intelligence/core_message.md`
3. `docs/planning/active/nh-trading-intelligence/north_star.md`
4. `docs/planning/active/nh-trading-intelligence/todo.md`
5. 필요한 코드와 테스트

긴 배경 문서는 막힐 때만 archive/reference에서 읽는다.

## Build & Verify

```bash
python main.py --full --profile nh-trading-v1
pytest -q tests/test_nh_trading_memo.py tests/test_nh_trading_profile.py
python -m compileall main.py pipeline/app pipeline/phases
```

참고:
- `python main.py --help` 는 현재 별도 import 오류가 있을 수 있으므로 보조 검증으로만 본다.

## Core Files

| Path | Role |
|------|------|
| `main.py` | CLI 진입점 |
| `pipeline/app/profiles.py` | 실행 경계와 기본 profile |
| `pipeline/schemas.py` | full artifact `EIMASResult` |
| `pipeline/nh_memo_view.py` | thin artifact `NHTradingDeskMemoV0` |
| `pipeline/role_profiles.py` | 직무군별 self-intro 해석층 |
| `tests/test_nh_trading_*.py` | NH Trading 경계 검증 |

## Default Path

```text
main.py
  -> phase execution
  -> EIMASResult
  -> NHTradingDeskMemoV0
```

기본 데모는 `nh-trading-v1` 기준이다.

## Anti-Patterns

- 기본 경로에 자동매매, trade plan, 크립토 데모를 다시 올리기
- 메모 경계를 문서로만 설명하고 profile/test에 반영하지 않기
- Trading 프로젝트를 IT 개발 포트폴리오처럼 설명하기

## Rule of Thumb

- active 문서는 얇게 유지한다.
- 제약은 코드, 스키마, 테스트로 옮긴다.
- narrative는 archive로 보낸다.
