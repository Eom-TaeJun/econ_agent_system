# eco_system — AI 참조 문서

## 실행

```bash
python main.py --quick                  # 빠른 분석 (기본 프로필)
python main.py --full                   # 전체 분석
python main.py --profile ra_equity      # 해외주식 RA 모드
python main.py --profile quant --full   # 퀀트 + 전체 분석
python main.py --profile macro          # 매크로 모드
python main.py --list-profiles          # 프로필 목록 확인
```

## Profile 구조 (직무별 튜닝)

범용 엔진(phases/) 위에 profile을 오버레이해서 직무별로 튜닝.
**개별 모델을 추가하는 게 아니라 config 오버레이 방식.**

```
profiles/
  base.yaml        ← 공통 기본값 (직접 실행 X)
  ra_equity.yaml   ← 해외주식 RA (섹터/어닝 중심)
  quant.yaml       ← 퀀트 (팩터/LASSO 중심)
  macro.yaml       ← 매크로 (금리/FX/크로스에셋 중심)
core/
  profile.py       ← load_profile("ra_equity") → base + 오버레이 병합
```

새 직무 추가: `profiles/[name].yaml` 파일만 생성, 코드 수정 불필요.
```yaml
name: "new_profile"
extends: base
# 바꾸고 싶은 항목만 오버라이드
data:
  tickers:
    extra: [AAPL, NVDA]
agents:
  system_prompt_overlay: |
    직무별 추가 지시사항
```

## 고정 구조 (변경 금지)

- Phase: collect → analyze → report (3개 고정)
- 에이전트: research, analysis, orchestrator (3개 고정)
- 저장소: DB 없음, outputs/ 하위 JSON만

## 빠른 참조

| 목적 | 파일 |
|------|------|
| 스키마 변경 | `core/schemas.py` |
| API 키 설정 | `core/config.py` |
| 데이터 수집 로직 | `phases/collect.py` |
| 분석 로직 | `phases/analyze.py` |
| 에이전트 추가 | `agents/base.py` 상속 |

## EIMAS 참조 경로

EIMAS에서 로직을 가져올 때 참조:
- 스키마: `~/projects/autoai/eimas/core/schemas.py`
- 에이전트 베이스: `~/projects/autoai/eimas/agents/base_agent.py`
- 수집: `~/projects/autoai/eimas/pipeline/collectors.py`
