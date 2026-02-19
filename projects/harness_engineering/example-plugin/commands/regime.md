---
description: 현재 시장 레짐 빠른 판단 (Growth-Inflation Matrix)
allowed-tools: Read, Bash
---

현재 거시경제 레짐을 빠르게 판단하라.

**수집할 지표 (최근 3개월 데이터):**

| 카테고리 | 지표 | 방향 기준 |
|----------|------|----------|
| 성장 | GDP QoQ SAAR, ISM Manufacturing, 산업생산 | 전기대비 |
| 인플레이션 | Core CPI YoY, Core PCE YoY, Breakeven 10Y | 전년대비 |

**판단 기준:**
- 성장 ↑ = 최근 GDP > 2.0% SAAR, ISM > 50
- 성장 ↓ = GDP < 1.5% SAAR, ISM < 50 연속 2개월
- 인플레이션 ↑ = Core CPI YoY > 3.0% 또는 상승 추세
- 인플레이션 ↓ = Core CPI YoY < 2.5% 또는 하락 추세

**출력 형식:**

```
현재 레짐: [Goldilocks / Overheating / Stagflation / Recession]
확신도: [High / Medium / Low]

성장: [↑/→/↓] [근거 지표 + 수치]
인플레이션: [↑/→/↓] [근거 지표 + 수치]

모순 시그널: [있으면 명시, 없으면 "없음"]
다음 확인 일정: [주요 데이터 발표 일정]
```

복잡한 분석 없이 빠른 레짐 스냅샷을 제공하는 것이 목적이다. 5분 내 완료를 목표로 하라.
