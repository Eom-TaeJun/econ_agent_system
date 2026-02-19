---
name: fed-rate-forecasting
description: |
  CME FedWatch 데이터를 활용한 Fed 금리 기대 변화 예측 방법론.
  LASSO 변수 선택, Post-LASSO OLS, HAC 표준오차, Horizon 분리,
  Selection Frequency 분석 등 분석 시 자동 활성화된다.
  Treasury 변수 제외 규칙, 시계열 교차검증, 이상치 처리 포함.
version: 1.0.0
updated: 2026-02-20
source: projects/forecast/summary/METHODOLOGY_GUIDE.md
---

# Fed 금리 예측 방법론 표준

## 핵심 변수 설계

- **종속변수**: `d_Exp_Rate` = 기대금리 일별 변화 (bp 단위, 차분값)
- **관측 단위**: (meeting_date, asof_date) 패널

## 1. LASSO — 변수 선택

```python
from sklearn.linear_model import LassoCV
from sklearn.model_selection import TimeSeriesSplit

model = LassoCV(cv=TimeSeriesSplit(n_splits=5), max_iter=10000)
model.fit(X_scaled, y)
selected = X.columns[model.coef_ != 0]
```

**왜 LASSO**: 변수 50개+ 환경에서 sparsity → 핵심 변수만 선택
**왜 Ridge 아님**: 변수 선택이 목적 (예측 정확도 아님)

## 2. Treasury 변수 제외 (필수)

```python
EXCLUDE_PATTERNS = ['Treasury', 'US2Y', 'US10Y', 'RealYield', 'Term_Spread',
                    'DGS2', 'DGS5', 'DGS10', 'DGS30', 'T10Y2Y', 'DFII10']
```

**이유**: Simultaneity (동시결정) — Treasury 금리 ↔ Fed 금리 기대는 서로 결정.
포함 시 인과관계 오해석 (내생성 편향).

## 3. Horizon 분리

| Horizon | 기간 | 특성 | 주요 변수 |
|---------|------|------|----------|
| 초단기 | ≤30일 | 뉴스/공포 민감 | VIX, 이벤트 더미 |
| 단기 | 31–90일 | 중간 | 달러, 크레딧 스프레드 |
| 장기 | ≥180일 | 펀더멘털 | 기대인플레, 거시지표 |

```python
very_short = df[df['days_to_meeting'] <= 30]
short      = df[(df['days_to_meeting'] > 30) & (df['days_to_meeting'] <= 90)]
long_term  = df[df['days_to_meeting'] >= 180]
```

**왜 분리**: 단기는 노이즈, 장기는 펀더멘털 — 같은 모델로 설명 불가.

## 4. Post-LASSO OLS with HAC

```python
import statsmodels.api as sm

# LASSO 선택된 변수만으로 OLS
ols = sm.OLS(y, X[selected]).fit(cov_type='HAC', cov_kwds={'maxlags': 5})
```

**2단계 이유**:
- LASSO: 변수 선택 (p-value 없음, 계수 축소됨)
- Post-OLS: 통계적 추론 (p-value, 신뢰구간)

**HAC 이유**: 시계열의 자기상관 + 이분산 → 일반 OLS는 p-value 과소추정.

## 5. Selection Frequency (Robustness)

```python
# Rolling window에서 각 변수의 선택 빈도 계산
# Selection Frequency > 50%: 안정적으로 중요한 변수
# Sign Consistency > 80%: 부호 일관성 (해석 신뢰)
```

**왜 필요**: LASSO 선택은 불안정할 수 있음. 여러 window에서 반복 선택된 변수만 신뢰.

## 6. ADF 검정 (비정상성 확인)

```python
from statsmodels.tsa.stattools import adfuller
result = adfuller(series)
# p < 0.05 → 정상(stationary) → OK
# p ≥ 0.05 → 비정상 → 차분 필요
```

**왜 필수**: 비정상 시계열 간 회귀 = Spurious Regression (허구적 상관).

## 결과 해석 기준

| 패턴 | 해석 |
|------|------|
| 초단기만 유의 | 노이즈/공포 지표 |
| 장기만 유의 | 펀더멘털 변수 |
| 전 구간 유의 | 핵심 설명 변수 |
| 부호 반전 | 구조적 변화 가능성 |

**부호 불일치 시**: 데이터 기간 차이 or Omitted Variable — 두 결과 모두 보고.

## 주요 변수 카테고리

| 카테고리 | 변수 | Fed와의 관계 |
|----------|------|-------------|
| Credit | `d_Spread_Baa`, `Ret_HighYield_ETF` | 스프레드↑ → 완화 기대↑ |
| FX | `Ret_Dollar_Idx` | 달러↑ → 긴축 기대↑ |
| Equity | `Ret_SP500`, `d_VIX` | 주식↓ / VIX↑ → 완화 기대↑ |
| Inflation | `d_Breakeven5Y`, `CPI_Released` | BEI↑ → 긴축 기대↑ |

## 전처리 파이프라인

```python
# 1. 차분 (비정상 → 정상)
df['d_Exp_Rate'] = df.groupby('meeting_date')['exp_rate_bp'].diff()

# 2. 이상치 마킹 (삭제 아님)
df['outlier_flag'] = (df['d_Exp_Rate'].abs() > 3 * df['d_Exp_Rate'].std()).astype(int)

# 3. 스케일링 (LASSO 전 필수)
from sklearn.preprocessing import StandardScaler
X_scaled = StandardScaler().fit_transform(X)
```

---
상세 방법론: `references/full-methodology.md`
원본 코드: `projects/forecast/forecasting_20251218.py`
