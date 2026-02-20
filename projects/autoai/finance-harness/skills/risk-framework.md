# 리스크 평가 프레임워크

> Finance Harness risk-mgr 에이전트가 적용하는 리스크 계산 및 판단 기준.
> 모든 투자 판단과 포트폴리오 변경 전 적용 필수.

---

## 1. VaR (Value at Risk)

### 계산 방법
```python
import numpy as np

def calculate_var(returns: np.ndarray, confidence: float = 0.95) -> float:
    """Historical VaR calculation."""
    return -np.percentile(returns, (1 - confidence) * 100)

def calculate_cvar(returns: np.ndarray, confidence: float = 0.95) -> float:
    """Conditional VaR (Expected Shortfall)."""
    var = calculate_var(returns, confidence)
    return -returns[returns < -var].mean()
```

### 임계값
| 수준 | VaR (95%) | 판단 |
|------|-----------|------|
| 안전 | <2% | 승인 |
| 주의 | 2-5% | 조건부 승인 |
| 경고 | 5-10% | 포지션 축소 권고 |
| 위험 | >10% | 승인 거부 |

---

## 2. MDD (Maximum Drawdown)

```python
def calculate_mdd(prices: np.ndarray) -> float:
    """최대낙폭 계산."""
    peak = np.maximum.accumulate(prices)
    drawdown = (prices - peak) / peak
    return abs(drawdown.min())
```

### 임계값
| MDD 수준 | 신호 | 조치 |
|---------|------|------|
| <10% | 정상 | 유지 |
| 10-15% | 주의 | 모니터링 강화 |
| 15-25% | 경고 | 자동 알림 발송 |
| >25% | 위험 | 즉각 포지션 검토 |

---

## 3. 집중 리스크

### 포지션 집중도
- **단일 포지션 > 포트폴리오 5%**: 경고
- **단일 섹터 > 30%**: 경고
- **단일 국가 > 50%**: 경고

### 상관관계 리스크
- **두 자산 간 상관계수 > 0.8**: 경고 (분산 효과 소멸)
- **포트폴리오 평균 상관계수 > 0.6**: 위험

```python
import pandas as pd

def check_concentration_risk(weights: dict, returns_df: pd.DataFrame) -> dict:
    """집중 리스크 확인."""
    warnings = []

    # 포지션 집중도
    for ticker, weight in weights.items():
        if weight > 0.05:
            warnings.append(f"CONCENTRATION: {ticker} = {weight:.1%} > 5% limit")

    # 상관관계
    corr_matrix = returns_df.corr()
    for i in range(len(corr_matrix)):
        for j in range(i+1, len(corr_matrix)):
            if corr_matrix.iloc[i, j] > 0.8:
                warnings.append(
                    f"CORRELATION: {corr_matrix.index[i]} & {corr_matrix.columns[j]} "
                    f"= {corr_matrix.iloc[i, j]:.2f} > 0.8"
                )

    return {"warnings": warnings, "count": len(warnings)}
```

---

## 4. 리스크 등급 (1-5)

| 등급 | 의미 | 판단 |
|------|------|------|
| 1 | 매우 낮음 | 즉시 승인 |
| 2 | 낮음 | 승인 |
| 3 | 보통 | 조건부 승인 (조건 명시) |
| 4 | 높음 | 포지션 축소 권고 후 승인 |
| 5 | 매우 높음 | 거부 |

---

## 5. 브로커 실행 승인 프로토콜

```
[ risk-mgr 승인 절차 ]

1. VaR 계산 → 임계값 확인
2. MDD 계산 → 임계값 확인
3. 집중 리스크 체크
4. 상관관계 체크
5. 종합 리스크 등급 산정

→ 등급 1-2: 즉시 승인 (APPROVED)
→ 등급 3:   조건부 승인 (CONDITIONAL: 조건 명시)
→ 등급 4:   축소 후 승인 (REDUCE: 축소 비율 명시)
→ 등급 5:   거부 (DENIED: 이유 명시)
```

**규칙:** risk-mgr 승인 없이 place_order 실행 불가.
