# 경제학 분석 방법론 표준

> Finance Harness 에이전트가 거시경제 분석 시 준수해야 할 방법론 기준.
> FRED 데이터 처리, 거시경제 지표 분석, LASSO 회귀, 시계열 분석 작업에 적용.

---

## 1. 변수 선택 방법론

### LASSO (L1 정규화)
- Sparsity를 통한 핵심 변수 자동 선택
- 정규화 강도(λ): Cross-validation으로 결정
- 계수가 0인 변수는 모델에서 자동 제외

### Treasury 관련 변수 제외 규칙
**이유:** Simultaneity(동시성) 문제 — Fed 금리와 Treasury 수익률은 상호 인과관계를 가져 편향 발생
**제외 대상:** DGS2, DGS5, DGS10, DGS30, T10YIE (물가연동채), TERM 스프레드
**대안:** Libor-OIS 스프레드, Credit 스프레드 (BBB-AAA)

---

## 2. 분석 Horizon 분리

| 구분 | 기간 | 적합 지표 |
|------|------|----------|
| 초단기 | ≤30일 | VIX, 일간 수익률, 거래량 |
| 단기 | 31~90일 | CPI, 고용 지표, ISM |
| 장기 | ≥180일 | GDP, 구조적 변화, 섹터 로테이션 |

**규칙:** Horizon별로 별도 모델 적합. 혼합 금지.

---

## 3. VIX 분해 (Bekaert et al. 2022)

```
VIX² = 불확실성(Uncertainty) + 리스크 선호(Risk Appetite)
```

- **불확실성**: 미래 변동성의 실제 기댓값 (경제 상황)
- **리스크 선호**: 투자자의 위험 감수 의지 (심리적 요인)
- VIX 급등 시: 두 성분 분리 분석 필수
- 데이터 출처: FRED `VIXCLS`

---

## 4. 결과 보고 기준

### 필수 항목
- **95% 신뢰구간 (CI)** 항상 명시: [하한, 상한]
- **p-value** 또는 **t-통계량** 포함
- **R²** 또는 **조정 R²** 명시

### 금지 표현
- "상관관계가 있으므로 X가 Y를 유발한다" → **인과관계 혼동 금지**
- "높은 상관관계" → 반드시 상관계수 수치 명시 (r=0.72 등)

### 계절조정 표기
- 계절조정 데이터: **(SA)** 표기
- 비조정 데이터: **(NSA)** 표기
- FRED 계절조정 시리즈: 대부분 SA

---

## 5. 주요 FRED 시리즈 ID

| 지표 | Series ID | 주기 |
|------|-----------|------|
| 실질 GDP | GDP | 분기 |
| 소비자물가 | CPIAUCSL | 월 |
| 핵심 PCE | PCEPILFE | 월 |
| 실업률 | UNRATE | 월 |
| Fed Funds Rate | FEDFUNDS | 월 |
| VIX | VIXCLS | 일 |
| S&P 500 | SP500 | 일 |
| 10년 국채 | DGS10 | 일 |

---

## 6. Granger 인과관계 검정

```python
from statsmodels.tsa.stattools import grangercausalitytests

# 최대 랙: 4 (분기 데이터) 또는 12 (월간 데이터)
results = grangercausalitytests(data[['y', 'x']], maxlag=4)
# p < 0.05 → X가 Y를 Granger 인과
```

**해석 주의:** Granger 인과 ≠ 실제 인과. 예측력 우위를 의미.
