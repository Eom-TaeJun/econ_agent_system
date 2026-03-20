# GFSI (Global Fear & Stress Index) 설계서

> 버전 0.3.0 | 2026-03-20

---

## 1. 왜 만드는가

**VIX의 한계**: S&P 500 옵션 내재변동성만 반영. 미국 장 마감(16:00 ET) 후, 주말, 공휴일에는
시장이 "눈 감은 상태"다. 크립토는 24/7 거래되고, 지정학 사건(전쟁, 제재)은 장 밖에서 터진다.

**GFSI의 목표**:
1. VIX가 놓치는 24/7 글로벌 리스크를 실시간 포착
2. 각 채널이 VIX를 **몇 시간/며칠 선행**하는지 실증 검증
3. 어떤 투자 목표(단기매매, 중기포지셔닝, 테일리스크)에서 어떤 채널이 유의미한지 식별
4. VIX에 이미 반영된 정보(이중반영)를 걸러내고 **잔차 정보**만 추출

---

## 2. 점수 체계

```
GFSI: 0 ─── 20 ─── 40 ─── 60 ─── 80 ─── 100
      CRISIS  STRESS  NEUTRAL  EXPANSION  EUPHORIA
      극단공포  스트레스  중립     확장       과열
```

- **0에 가까울수록**: 공포, 유동성 이탈, 위험 회피
- **100에 가까울수록**: 탐욕, 자본 유입, 위험 선호
- VIX와 **역방향** (VIX↑ = 공포, GFSI↓ = 공포)

---

## 3. 5개 채널 구성 (v0.3)

### 종합 산출 공식

```
GFSI = Σ(채널 점수 × 가중치 × 데이터품질) / Σ(가중치 × 데이터품질)
```

| # | 채널 | 가중치 | 보는 것 | 24/7 여부 | 소스 유형 |
|---|------|--------|---------|-----------|-----------|
| 1 | crypto_vol | 25% | BTC 변동성 구조 + ETH/BTC | O | 가격 기반 |
| 2 | stable_flow | 20% | 스테이블코인·DeFi 자본 흐름 | O | 온체인 |
| 3 | geo_stress | 25% | GPR 텍스트 + 유가·금 프록시 | O | 텍스트+가격 |
| 4 | news_stress | 15% | EPU 경제정책 불확실성 | X (일일) | 텍스트 기반 |
| 5 | liquidity | 15% | Fed RRP + TGA | X (일일) | 구조적 배경 |

### v0.1 → v0.3 채널 변경

**삭제 2개**:
- `currency` (DXY/JPY): VIX와 동시 반응 (FX는 US 거래시간과 겹침), 독립 정보 부족. Bruno & Shin(2015)에 따르면 DXY는 VIX와 0.7 이상 상관.
- `sentiment` (F&G Index): 예측력 ~52% (동전던지기), crypto_vol과 이중반영 (F&G의 25%가 BTC 변동성 기반).

**추가 1개**:
- `news_stress` (EPU): v0.1은 6채널 전부 가격 파생이었음. 전쟁/정책변화는 뉴스가 먼저(0분), 가격 반응(분~시간), GFSI 수집(시간~일). 텍스트 기반 채널 없이는 이벤트 포착 시점이 늦음. EPU(Baker, Bloom & Davis)는 정책 불확실성, GPR(Caldara & Iacoviello)은 지정학 텍스트 — 둘 다 학술적 근거가 탄탄.

---

## 4. 채널별 점수 산출 — 상세 수식

모든 채널은 내부에 2-3개 **서브지표**를 가진다.
각 서브지표는 `linear_scale(값, 하한, 상한, invert?)` → 0-100으로 변환.

```python
linear_scale(value, low, high, invert=False):
    score = (value - low) / (high - low) × 100
    if invert: score = 100 - score
    return clamp(score, 0, 100)
```

---

### 채널 1: crypto_vol (BTC 변동성) — 가중 25%

**의미**: BTC 시장의 단기 변동성이 장기 대비 얼마나 높은가.
높으면 → 스트레스, 낮으면 → 안정. 유일한 완전 24/7 가격 채널.

| 서브지표 | 비중 | 입력 범위 | 변환 | 해석 |
|----------|------|----------|------|------|
| **btc_vol_ratio** (20d÷60d 실현변동성) | 60% | [0.49, 1.95] | invert | 0.5→안정(100점), 2.0→급등(0점) |
| **btc_return_7d** (7일 수익률 %) | 25% | [-15, +15] | 정방향 | -15%→0점, +15%→100점 |
| **eth_btc_ratio 변화** (현재÷20d평균) | 15% | [-10%, +10%] | 정방향 | ETH 상대강세=리스크온→높은 점수 |

---

### 채널 2: stable_flow (스테이블코인·DeFi 흐름) — 가중 20%

**의미**: 법정화폐→크립토 자본이 유입(스테이블코인 발행↑)되고,
온체인 활동이 증가(DeFi TVL↑)하면 → 리스크 온. VIX에 전혀 안 잡히는 독립 정보.

| 서브지표 | 비중 | 입력 범위 | 변환 | 해석 |
|----------|------|----------|------|------|
| **stablecoin_mcap_change_7d** (%) | 60% | [-2%, +2%] | 정방향 | 유출(-2%)→0점, 유입(+2%)→100점 |
| **defi_tvl_change_7d** (%) | 40% | [-5%, +5%] | 정방향 | TVL감소→0점, 증가→100점 |

---

### 채널 3: geo_stress (지정학 스트레스) — 가중 25%

**의미**: GPR 텍스트 시그널을 primary로, 유가·금 가격을 confirmation으로 사용.
GPR이 없으면 가격 프록시만으로 폴백.

v0.3에서 GPR Index(Caldara & Iacoviello 2022) 추가. 신문 키워드 빈도에서 지정학 위험을 추출하는 학술 지표로, 가격 변동보다 선행.

| 서브지표 | 비중 (GPR 있음) | 비중 (GPR 없음) | 입력 범위 | 변환 | 해석 |
|----------|-----------------|-----------------|----------|------|------|
| **GPR Index** | 40% | — | [50, 300] | invert | 50→안정(100점), 300→위기(0점) |
| **oil_gold_corr_20d** | 25% | 50% | [-0.5, 0.8] | invert | 디커플링→안정, 동조→긴장 |
| **oil_change_7d** (%) | 20% | 30% | [-10%, +10%] | invert | 급등→0점, 하락→100점 |
| **gold_vs_ma20** (%) | 15% | 20% | [-5%, +5%] | invert | MA 위→안전자산수요→긴장 |

---

### 채널 4: news_stress (뉴스 스트레스) — 가중 15%

**v0.3 신규 채널**

**의미**: EPU(Economic Policy Uncertainty, Baker, Bloom & Davis)를 통해 정책 불확실성을 포착.
무역전쟁, 금리정책, 규제 변화 등 비군사적 리스크. FRED USEPUINDXD 시리즈 (일일).

| 서브지표 | 비중 | 입력 범위 | 변환 | 해석 |
|----------|------|----------|------|------|
| **EPU 현재 수준** | 70% | [50, 400] | invert | 50→안정(100점), 400→위기(0점) |
| **EPU 7일 변화** | 30% | [-100, +100] | invert | 급등(+100)→스트레스, 개선(-100)→100점 |

FRED 키 없으면 `data_quality=0`으로 자동 제외.

---

### 채널 5: liquidity (유동성) — 가중 15%

**의미**: Fed 시스템의 실질 유동성. Pozsar(2022) 'plumbing' 프레임워크 기반.

| 서브지표 | 비중 | 입력 범위 | 변환 | 해석 |
|----------|------|----------|------|------|
| **RRP** | 60% | 아래 참조 | 아래 참조 | RRP 감소→유동성 방출 |
| **TGA** | 40% | 아래 참조 | 아래 참조 | 적정 범위→안정 |

**RRP 특수 처리 (v0.2 수정)**:
```
rrp < $50B → 75점 고정 (near-zero에서 퍼센트 변화율 무의미)
rrp ≥ $50B → linear_scale(주간 절대 변동, -$50B, +$50B, invert)
```

**TGA 비대칭 3구간 (v0.2 수정)**:
```
중심: $650B (재무부 목표 ~$600B + 2024-26 평균)

① 위기구간: TGA < $450B (중심 - $200B)
   → 부채한도 위기 수준 → 0-30점

② 흡수구간: TGA > $1,000B (중심 + $350B)
   → 유동성 과잉 흡수 → 30-70점

③ 적정구간: $450B ≤ TGA ≤ $1,000B
   → 정상 운영 → 70-100점
```

FRED 키 없으면 `data_quality=0`으로 자동 제외.

---

## 5. 데이터 품질 처리

각 채널의 `data_quality` (0-1)는 종합 가중치에 곱해진다.

```
실효 가중치 = 기본 가중치 × data_quality
```

| 상황 | data_quality | 효과 |
|------|-------------|------|
| 모든 데이터 정상 | 1.0 | 정상 가중치 |
| BTC 데이터 실패 | 0.7 | crypto_vol 가중치 70%로 축소 |
| FRED 키 없음 | 0.0 | news_stress, liquidity 완전 제외 |
| DefiLlama 다운 | 0.8 | stable_flow 가중치 80%로 축소 |
| GPR CSV 다운 | 0.8 | geo_stress의 GPR 빠지고 가격 프록시만 사용 |

---

## 6. 선행성 검증 계획

20일 이상 데이터 축적 후 `--analyze` 플래그로 자동 실행.

### 검증 1: Cross-Correlation (교차상관)
각 채널 점수 시계열을 ±10일 lag로 VIX와 상관 계산. 최대 상관의 lag = 최적 선행/후행 일수.

### 검증 2: Granger Causality (인과 관계)
H0: 채널 X가 VIX를 Granger-cause하지 않음. p < 0.05이면 기각.

### 검증 3: R² 이중반영 체크
VIX ~ 채널 선형회귀 → R². 높으면 이미 VIX에 반영된 정보. residual_info = 1 - R².

### 검증 4: 수익률 예측력 (30일 후)
GFSI 레벨 vs 30일 후 BTC·SPX 수익률.

---

## 7. 데이터 소스

| 소스 | API | 키 필요 | 비용 | 채널 |
|------|-----|---------|------|------|
| yfinance | Python 패키지 | X | 무료 | crypto_vol, geo_stress |
| DefiLlama | REST | X | 무료 | stable_flow |
| Caldara & Iacoviello | CSV | X | 무료 | geo_stress (GPR) |
| FRED | REST | O | 무료 | news_stress (EPU), liquidity (RRP/TGA) |

---

## 8. 실행 방법

```bash
cd ~/projects/eco_system_v2

# 일일 수집 + 산출 + 저장
python -m experimental.gfsi.cli

# 선행성 분석 포함 (20일 이상 기록 필요)
python -m experimental.gfsi.cli --analyze

# 저장 없이 테스트
python -m experimental.gfsi.cli --dry-run

# JSON 출력 (파이프라인 연동용)
python -m experimental.gfsi.cli --json

# 전체 산출 과정 추적
python -m experimental.gfsi.cli --explain

# 과거 기록 리포트
python -m experimental.gfsi.cli --report-only
```

---

## 9. 향후 과제

- [ ] 20일 기록 축적 후 선행성 분석 첫 실행
- [ ] 가중치 최적화 (고정 → 레짐별 적응형)
- [ ] eco_system_v2 메인 파이프라인에 GFSI 채널 통합
- [ ] 주말 갭 분석 (금요일 GFSI → 월요일 SPX 갭)
- [ ] 목표별 유의미 채널 리포트 (단기/중기/테일리스크)
- [ ] VIX 잔차 전용 지표 (GFSI - VIX 설명 부분) 설계
- [ ] GPR 데이터 소스 안정화 (현재 CSV 404 이슈 — 로컬 폴백 구현됨)

---

## 부록: 임계값 근거 일람

| 상수 | 값 | 근거 | 버전 |
|------|-----|------|------|
| BTC_VOL_RATIO_HIGH | 1.5 | [설계] 20d/60d 비율 — 단기 변동성 급등 | v0.1 |
| BTC_VOL_RATIO_LOW | 0.7 | [설계] 단기 변동성 수축 — 안정기 | v0.1 |
| STABLE_MCAP_CHANGE_HIGH | +2% | [설계] 7일 시총 변화 — 의미있는 유입 | v0.1 |
| STABLE_MCAP_CHANGE_LOW | -2% | [설계] 7일 시총 변화 — 의미있는 유출 | v0.1 |
| OIL_GOLD_CORR_HIGH | 0.6 | [검증] 20일 상관 — 장기평균 0.42, 위기시 0.78. Reboredo(2013) | v0.1 |
| GPR_LOW | 50 | [학술] GPR 안정기 하한. 역사적 평균 ~100. Caldara & Iacoviello(2022) | v0.3 |
| GPR_HIGH | 300 | [학술] 주요 위기 수준. 러-우 ~400, 9/11 ~500 | v0.3 |
| EPU_LOW | 50 | [학술] EPU 안정기 하한. 역사적 평균 ~100-130. Baker, Bloom & Davis | v0.3 |
| EPU_HIGH | 400 | [학술] 위기 수준. COVID ~600, 정부셧다운 ~300+ | v0.3 |
| TGA_CENTER_B | $650B | [검증] 재무부 2023 가이던스 ~$600B + 2024-26 평균 | v0.2 |
| TGA_DEVIATION_LOW_B | $200B | [검증] 중심 대비 하한. 2023 부채한도 위기시 ~$50B | v0.2 |
| TGA_DEVIATION_HIGH_B | $350B | [검증] 중심 대비 상한. 2021 최고 ~$1.6T | v0.2 |
| RRP_NEAR_ZERO_B | $50B | [검증] 2025말 RRP ≈ $0 도달. 퍼센트 변화율 무의미 경계 | v0.2 |
| RRP_ABS_CHANGE_B | $50B | [검증] 주간 절대 변동 기준. 2022-24 RRP 주간 변동 참조 | v0.2 |
| LEAD_LAG_MAX_DAYS | 10 | [설계] 최대 선행/후행 탐색 범위 | v0.1 |
| GRANGER_P_VALUE | 0.05 | [학술] 5% 유의수준 | v0.1 |

`[설계]` = 백테스트 미검증. `[검증]` = 학술/실증 데이터 확인 완료. `[학술]` = 학술 표준.

---

## 부록: 변경 이력

### v0.3.0 (2026-03-20) — 채널 구조 개편

**변경 이유**: v0.1의 6채널이 모두 가격 파생이어서 텍스트/뉴스 이벤트 포착 불가. 동시에 DXY/JPY(currency)와 F&G(sentiment)는 VIX 또는 crypto_vol과 이중반영.

**삭제 2개**:
1. `currency` (DXY/JPY) — VIX와 상관 0.7+, FX 거래시간이 US 장과 겹쳐 독립 정보 부족
2. `sentiment` (F&G) — 예측력 ~52%, crypto_vol과 25% 이중반영

**추가 1개**:
3. `news_stress` (EPU) — Baker, Bloom & Davis 학술 지표. FRED USEPUINDXD로 일일 수집

**변경 3개**:
4. `geo_stress` — GPR Index를 primary(40%)로 추가, 가격 프록시를 confirmation으로 격하
5. 가중치 재조정: crypto_vol 20→25%, stable_flow 15→20%, geo_stress 20→25%, new news_stress 15%, liquidity 15%
6. `cli.py` — 과거 v0.1 JSON 호환 필터 추가 (삭제된 채널명 무시)

**학술 근거 추가**:
- Caldara & Iacoviello (2022) — GPR Index
- Baker, Bloom & Davis — EPU Index

### v0.2.0 (2026-03-20) — 임계값 검증 및 수정

**수정 3건**:

1. **RRP 채널**: 퍼센트 변화율 → 절대 금액 + near-zero 분기
   - 문제: RRP≈$0일 때 -100% → 무조건 100점
   - 수정: `rrp < $50B → 75점 고정` + 절대 금액 기반

2. **TGA 채널**: 중심값 + 비대칭 처리
   - 문제: $500B 중심 (너무 낮음) + 대칭 편차
   - 수정: 중심 $650B, 비대칭 3구간

3. **DXY 범위**: [0, 5%] → [0, 3.5%]
   - 문제: DXY 20일 5%는 10년 1회 극단
   - 수정: 상한 3.5%로 축소 (v0.3에서 currency 채널 삭제로 이 수정은 더 이상 사용되지 않음)

### v0.1.0 (2026-03-19) — 초판

6채널 (crypto_vol, stable_flow, geo_stress, currency, sentiment, liquidity) 구성.
