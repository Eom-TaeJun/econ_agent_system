---
description: "eco_system_v2 파이프라인 실행. --quick(기본), --full, --forecast 모드 지원."
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# /run — eco_system_v2 파이프라인 실행

## 사용법
```
/run              → --quick 모드 (AnalysisAgent만)
/run --full       → Analysis + Research + Quant 병렬 → Debate 순차
/run --forecast   → full + ForecastAgent 추가
/run --report     → 실행 후 MD/HTML 리포트 생성
```

## 실행 절차

1. **Pre-check**: 환경변수 확인 (`ANTHROPIC_API_KEY` 필수)
2. **Run**: `python main.py` + 해당 플래그
3. **Verify**: 출력 JSON 구조 확인
4. **Report**: `--report` 시 `outputs/report_*.md` 생성 확인

## 모드별 플래그 매핑

| 입력 | 실행 명령 |
|------|----------|
| `/run` | `python main.py --quick` |
| `/run --full` | `python main.py --full` |
| `/run --forecast` | `python main.py --forecast` |
| `/run --full --report` | `python main.py --full --report` |

## 결과 확인

실행 후 최신 output을 자동으로 읽어 핵심 지표를 요약:
- 합의 신호 (BULLISH/NEUTRAL/BEARISH)
- 신뢰도
- 에이전트별 판단 요약
- 레짐/리스크 (--full 이상)
