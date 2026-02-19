---
name: analysis-standards
description: |
  금융·경제 분석 결과를 코드로 작성하거나(Python/pandas/statsmodels),
  통계 모델을 적용하거나(회귀, LASSO, VAR, ARIMA), 분석 리포트를 작성하거나,
  데이터 시각화 코드를 생성할 때 활성화된다.
  일반 프로그래밍이나 비금융 분석에는 활성화하지 않는다.
version: 1.0.0
---

# 금융 분석 코드 & 방법론 표준

## Python 코드 컨벤션

```python
# 필수 임포트 순서
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple

# 금융 데이터
import yfinance as yf
import pandas_datareader.data as web  # FRED

# 통계/ML
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.stattools import adfuller, grangercausalitytests
from statsmodels.tsa.vector_ar.var_model import VAR
```

---

## 시계열 데이터 처리 원칙

### 필수 검증 단계
```python
def validate_series(df: pd.DataFrame, series_name: str) -> Dict:
    """시계열 데이터 품질 검증"""
    report = {
        "name": series_name,
        "length": len(df),
        "missing_pct": df.isnull().mean().to_dict(),
        "is_stationary": {},
        "date_range": (df.index.min(), df.index.max())
    }
    # ADF 단위근 검정
    for col in df.select_dtypes(include=np.number).columns:
        result = adfuller(df[col].dropna())
        report["is_stationary"][col] = result[1] < 0.05  # p-value < 0.05
    return report
```

### 변환 우선순위
1. 수준(Level) → 전년대비 변화율(YoY%) → 전기대비 변화율(MoM%)
2. 비정상(Non-stationary) → 1차차분 or 로그차분
3. 계절조정: X-13ARIMA 또는 `statsmodels.tsa.x13`

---

## 통계 모델 선택 기준

| 목적 | 권장 모델 | 주의사항 |
|------|----------|----------|
| 변수 선택 | **LASSO** (LassoCV) | Treasury 변수 제외 (simultaneity) |
| 단기 예측 | **ARIMA / SARIMA** | 정상성 확인 필수 |
| 다변량 예측 | **VAR** | lag 선택: AIC/BIC 기준 |
| 인과관계 | **Granger Causality** | 상관관계와 구분하여 해석 |
| 레짐 분류 | **HMM / Threshold** | 2-state가 기본 |
| 이상 탐지 | **Z-score + IQR** | 금융 데이터는 fat tail 주의 |

### LASSO 적용 시 필수 설정
```python
# Simultaneity Bias 방지: Treasury 변수 제외
EXCLUDE_FROM_LASSO = [
    'DGS2', 'DGS5', 'DGS10', 'DGS30',  # Treasury yields
    'T10Y2Y', 'T10Y3M',                   # Spreads
    'DFII10'                               # TIPS
]

scaler = StandardScaler()
lasso = LassoCV(
    cv=TimeSeriesSplit(n_splits=5),  # 반드시 TimeSeriesSplit (미래 누수 방지)
    max_iter=10000,
    random_state=42
)
```

---

## 시각화 표준

```python
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 차트 기본 설정
plt.rcParams.update({
    'figure.figsize': (12, 6),
    'axes.grid': True,
    'grid.alpha': 0.3,
    'axes.spines.top': False,
    'axes.spines.right': False
})

def plot_with_recession_bands(ax, series, title: str):
    """NBER 경기침체 구간 음영 포함 차트"""
    ax.plot(series.index, series.values, linewidth=1.5)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    # 경기침체 음영 (USREC from FRED)
    # add_recession_shading(ax)
```

---

## 리포트 구조 표준

분석 리포트는 반드시 아래 섹션을 포함:

1. **Executive Summary** (3줄 이내) — 핵심 결론만
2. **데이터 개요** — 소스, 기간, 품질 지표
3. **분석 결과** — 방법론과 수치 근거
4. **시그널 종합** — 긍정/부정/중립 시그널 분류
5. **리스크 요인** — 분석의 한계, 불확실성
6. **결론 및 함의** — 실행 가능한 인사이트

---

## 출력 파일 네이밍 컨벤션

```
outputs/
├── {topic}_{YYYYMMDD}.json      # 원시 분석 결과
├── {topic}_{YYYYMMDD}.md        # 텍스트 리포트
└── charts/
    └── {indicator}_{YYYYMMDD}.png
```
