---
name: eco-analysis-standards
description: |
  eco_system_v2의 정량분석 방법론 관련 작업 시 활성화.
  레짐 탐지(GMM, MA), 리스크 계산(VaR, CVaR), LASSO 모델,
  포트폴리오 최적화(HRP), 변동성 분석 등을 다룰 때.
version: 2.0.0
---

# 정량분석 방법론 표준

## 레짐 탐지 (Regime Detection)

**2-계층 분류** (`infrastructure/analysis/regime_service.py`):

### 계층 1: GMM 3-State
- sklearn `GaussianMixture(n_components=3)` on (Returns, VIX) 2D
- 컴포넌트 정렬: VIX 평균 기준 (lowest→Bull, highest→Bear)
- sklearn 미설치 시 규칙 기반 폴백 (Bull/Neutral/Bear 임계값)

### 계층 2: MA 크로스오버 + VIX
- 추세: 50일 MA vs 200일 MA 관계
- 변동성: VIX 절대 수준 (12/16/22/30 임계값)

**레짐 분류**:
| 레짐 | 조건 |
|------|------|
| Bull (Low Vol) | price > MA200 + VIX < 16 |
| Bull (High Vol) | price > MA200 + VIX >= 22 |
| Bear (Low Vol) | price < MA200 + VIX < 22 |
| Bear (High Vol) | price < MA200 + VIX >= 30 |
| Transition | 기타 |

**부가 지표**:
- RSI-14 (Wilder smoothing)
- 20일 모멘텀 (%)
- 52주 고점 대비 거리 (%)
- VIX 백분위 (최근 시계열 대비)

**전환 확률**: 최근 시계열에서 레짐 전환 빈도 추정 → `transition_probs`

**참고**: Hamilton(1989) Markov Switching Model 간소화 버전

## 리스크 계산

**지표** (`infrastructure/analysis/risk_service.py`):
- VaR 95% (Historical Simulation)
- CVaR / Expected Shortfall (tail 평균)
- 실현 변동성 (20일 rolling, 연환산)
- Max Drawdown

**리스크 수준 분류**:
| 수준 | 조건 |
|------|------|
| LOW | VIX < 16 + 양호한 추세 |
| MEDIUM | 16 <= VIX < 22 또는 수익률 곡선 역전 단독 |
| HIGH | 22 <= VIX < 30 또는 Bear 레짐 + VIX >= 16 |
| EXTREME | VIX >= 30 또는 (VIX >= 22 + 수익률 곡선 역전 < -0.5%) |

**수익률 곡선 반영**: 10Y Treasury - Fed Funds Rate 스프레드
- < -0.5%: 경기침체 경고 → 리스크 수준 승격

## QuantAgent 신호 계산

LLM 없이 score(-1 ~ +1) 누적 후 신호 결정:
- VIX 수준, SPX 30d 수익률, 레짐, 리스크, GMM 확률, 수익률 곡선, DXY, RSI
- score > 0.2 → BULLISH, score < -0.2 → BEARISH, 기타 → NEUTRAL
- confidence = min(1.0, 0.4 + |score|)

## Horizon 분리 (LASSO 사용 시, 미구현)
- 초단기: ≤30일
- 단기: 31-90일
- 장기: ≥180일
- Treasury 변수 제외 (동시성 편의 방지)
