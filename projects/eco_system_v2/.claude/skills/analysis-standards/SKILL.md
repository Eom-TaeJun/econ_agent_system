---
name: eco-analysis-standards
description: |
  eco_system_v2의 정량분석 방법론 관련 작업 시 활성화.
  레짐 탐지(GMM, MA), 리스크 계산(VaR, CVaR), LASSO 모델,
  포트폴리오 최적화(HRP), 변동성 분석 등을 다룰 때.
version: 1.0.0
---

# 정량분석 방법론 표준

## 레짐 탐지 (Regime Detection)

**방법론**: MA 크로스오버 + VIX 레벨 기반 분류
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

**참고**: Hamilton(1989) Markov Switching Model 간소화 버전

## 리스크 계산

**지표**:
- VaR 95%/99% (Historical Simulation)
- CVaR (Expected Shortfall)
- 실현 변동성 (20일 rolling)
- Max Drawdown

**리스크 수준 분류**:
| 수준 | 조건 |
|------|------|
| LOW | VIX < 16 + 양호한 추세 |
| MEDIUM | 16 <= VIX < 22 |
| HIGH | 22 <= VIX < 30 |
| EXTREME | VIX >= 30 또는 급격한 하락 |

## Horizon 분리 (LASSO 사용 시)
- 초단기: ≤30일
- 단기: 31-90일
- 장기: ≥180일
- Treasury 변수 제외 (동시성 편의 방지)
