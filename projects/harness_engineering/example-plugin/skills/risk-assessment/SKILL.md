# Risk Assessment — 리스크 평가 도메인 지식

> 이 스킬은 `agents/risk-mgr.md`가 참조하는 도메인 지식이다.
> AI는 이 파일을 수정하지 않는다.

---

## 리스크 측정 프레임워크

### 핵심 개념 계층

```
시스템 리스크 (Systemic Risk)
    ├── 시장 리스크 (Market Risk)     ← VaR, CVaR, 변동성
    ├── 유동성 리스크 (Liquidity)     ← 스프레드, 거래량
    ├── 신용 리스크 (Credit)          ← HY OAS, CDS
    └── 꼬리 리스크 (Tail Risk)       ← 극단 손실 시나리오
```

---

## VaR / CVaR 기준값

| 지표 | 정상 | 주의 | 경보 |
|------|------|------|------|
| 95% VaR (일간) | < 1.5% | 1.5–2.5% | > 2.5% |
| 99% VaR (일간) | < 2.5% | 2.5–4.0% | > 4.0% |
| CVaR (95%) | < 2.0% | 2.0–3.5% | > 3.5% |

**CVaR = Expected Shortfall**: VaR 초과 손실의 조건부 기대값.
VaR보다 꼬리 리스크를 더 잘 포착한다.

---

## Bekaert VIX 분해 (2013)

> VIX = Risk Appetite Component + Uncertainty Component

```
Risk Appetite ↑  → 투자자가 리스크 프리미엄 요구 상승 (공포 주도)
Uncertainty ↑    → 미래 불확실성 자체가 큰 상황 (정보 부재)

두 성분의 dominant에 따라 대응 전략이 달라진다:
- Risk Appetite 지배 → 헷지 비용 상승, 옵션 매수 유효
- Uncertainty 지배   → 포지션 축소, 현금 비중 확대
```

---

## 리스크 등급 매트릭스

| 등급 | VIX | HY OAS | 10Y-2Y | 행동 지침 |
|------|-----|--------|--------|---------|
| LOW | < 15 | < 300bp | 정상 | 리스크 온 허용 |
| MEDIUM | 15–25 | 300–500bp | 주시 | 헷지 점검 |
| HIGH | 25–35 | 500–700bp | 역전 | 익스포저 축소 |
| CRITICAL | > 35 | > 700bp | 역전→steepening | 즉시 경보 |

**즉시 경보 3중 조건** (모두 충족 시):
```
VIX > 25 AND HY OAS > 500bp AND (10Y-2Y 역전 후 steepening 시작)
```

---

## 시나리오 분석 표준

모든 리스크 평가는 3개 시나리오를 필수로 작성한다:

| 시나리오 | 확률 | 기준 |
|---------|------|------|
| 기본 (Base) | 60% | 현재 추세 지속, 1σ 이내 |
| 스트레스 (Stress) | 30% | 1–2σ 충격 (2022 금리 충격 급) |
| 꼬리 (Tail) | 10% | 2σ 초과 (2008 GFC, 2020 COVID 급) |

---

## 버블 탐지 (Greenwood, Shleifer & You 2019)

```
버블 경보 조건 (3개 이상 해당 시):
  □ 2년 수익률 ≥ 100%
  □ 변동성(σ)이 5년 평균 대비 +2σ 이상
  □ 섹터 IPO 발행량 전년 대비 급증
  □ P/E 낮지만 변동성 높은 상태 (디커플링)

합리적 붐과 버블의 차이: 변동성
  합리적 붐 → 가격 상승 + 낮은 변동성
  버블       → 가격 상승 + 높은 변동성 → 평균 -40% 폭락
```

---

## 한국 시장 특수 지표

| 지표 | 경보 기준 | 의미 |
|------|---------|------|
| 원달러 환율 | > 1,500 KRW | BOK 개입 임계 |
| 외국인 순매도 | 5거래일 연속 | 자본 유출 신호 |
| CD금리-기준금리 | > 50bp 괴리 | 단기 유동성 경색 |

---

## 리스크 평가 출력 스키마

```json
{
  "assessed_at": "ISO timestamp",
  "risk_grade": "LOW | MEDIUM | HIGH | CRITICAL",
  "alert": false,
  "var_95": 0.0,
  "cvar_95": 0.0,
  "vix_decomposition": {
    "vix_level": 0.0,
    "risk_appetite": 0.0,
    "uncertainty": 0.0,
    "dominant": "risk_appetite | uncertainty"
  },
  "scenarios": {
    "base":   { "probability": 0.6, "expected_return": 0.0, "max_drawdown": 0.0 },
    "stress": { "probability": 0.3, "expected_return": 0.0, "max_drawdown": 0.0 },
    "tail":   { "probability": 0.1, "expected_return": 0.0, "max_drawdown": 0.0 }
  },
  "key_risks": [],
  "monitoring_triggers": []
}
```

저장 위치: `outputs/context/risk_assessment.json`
