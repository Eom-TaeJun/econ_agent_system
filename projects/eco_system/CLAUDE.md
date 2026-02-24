# eco_system — AI 참조 문서

## 실행

```
python main.py --quick   # 빠른 실행
python main.py --full    # 전체 실행
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
