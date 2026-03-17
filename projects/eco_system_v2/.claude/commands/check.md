---
description: "최신 eco_system_v2 실행 결과를 요약. outputs/ 디렉토리에서 가장 최근 JSON을 읽어 핵심 지표를 보여준다."
allowed-tools: ["Bash", "Read", "Glob"]
---

# /check — 최신 결과 요약

## 절차

1. `outputs/` 디렉토리에서 가장 최근 `eco_*.json` 파일을 찾는다
2. JSON을 읽어 다음을 요약한다:
   - 분석 날짜
   - 합의 신호 + 신뢰도
   - 에이전트별 신호 테이블
   - 시장 데이터 스냅샷
   - 레짐/리스크 (있을 경우)
3. 리포트 파일이 있으면 (`outputs/report_*.md`) 경로도 알려준다

## 출력 형식

```
날짜: 2026-03-17
신호: BULLISH (72%)
에이전트:
  - analysis: BULLISH (0.75)
  - research: BULLISH (0.68)
  - quant: NEUTRAL (0.60)
레짐: Bull (Low Vol)
리스크: LOW
```
