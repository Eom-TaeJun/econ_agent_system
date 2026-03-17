---
name: eco-domain-guide
description: |
  eco_system_v2 도메인 모델 작업 시 활성화.
  Signal, MarketData, EconomicSignal, ConsensusService, RegimeResult,
  RiskMetrics, ForecastResult, DebateResult 등 도메인 객체를 다룰 때.
  domain/ 디렉토리 파일을 읽거나 수정할 때.
version: 1.0.0
---

# eco_system_v2 도메인 가이드

## 핵심 원칙
- `domain/`은 stdlib만 허용 (import anthropic, httpx, yfinance 절대 금지)
- 모든 VO는 `@dataclass(frozen=True)` + `to_dict()` 패턴
- Enum은 `str, Enum` 상속 (JSON 직렬화 용이)

## 도메인 객체 맵

| 객체 | 파일 | 역할 |
|------|------|------|
| `Signal` | signal.py | BULLISH/NEUTRAL/BEARISH enum |
| `EconomicSignal` | signal.py | 에이전트 판단 결과 VO |
| `MarketData` | market_data.py | 거시경제 스냅샷 VO |
| `ConsensusService` | consensus.py | 다수결 합의 도메인 서비스 |
| `MarketRegime` | regime.py | 시장 레짐 enum (5종) |
| `RegimeResult` | regime.py | 레짐 탐지 결과 VO |
| `RiskLevel` | risk.py | 리스크 수준 enum |
| `RiskMetrics` | risk.py | 리스크 지표 VO |
| `HorizonType` | forecast.py | 전망 시계 enum |
| `ForecastResult` | forecast.py | 전망 결과 VO |
| `DebateResult` | debate.py | 토론 합의 결과 VO |
| `ReportSection` | report.py | 리포트 섹션 VO |
| `AnalysisReport` | report.py | 최종 리포트 VO |

## 경계 규칙
```
domain/ → stdlib만
agents/ → domain + infrastructure 임포트 가능
infrastructure/ → 외부 라이브러리 허용
```
