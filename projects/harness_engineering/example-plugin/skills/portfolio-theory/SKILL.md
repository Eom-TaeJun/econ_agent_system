---
name: portfolio-theory
description: |
  포트폴리오 구성·최적화·리스크 분해 작업 시 활성화된다.
  Sharpe Ratio 계산, Mean-Variance Frontier, HRP, 공분산 행렬 역행렬 문제,
  CAPM/팩터 모델, ETF 분석, 알파/베타 분리, 자산 배분 전략 관련 작업 포함.
  단순 가격 조회나 거시경제 이슈에는 활성화하지 않는다.
version: 1.0.0
---

# 포트폴리오 이론 프레임워크

## 핵심 목적함수

```
포트폴리오의 목표:
  주어진 리스크에서 수익 극대화
  OR 주어진 수익에서 리스크 최소화

수익: forecasting 가능 (측정 가능)
리스크: Var, Cov matrix → 이게 진짜 어려운 문제
```

**Sharpe Ratio:**
```
SR = (R - Rf) / σ
ETF도 SR은 커지지만 연간 절대 수익은 작을 수 있음
단기투자(3개월)가 더 유리한 경우도 존재
```

---

## 리스크 분해 구조

```
개별 주식 기대수익 = α + β × E(Rm)  [CAPM]

삼성전자 리턴 = α + b₁·R(KOSPI) + b₂·FIVUSIQ + b₃·PBR

리스크 분해:
  Index(KOSPI, NASDAQ) → 전체의 70-80%
  Factor(PBR, firmsize, EPS, 성장) → ~20%
  Macro 지수 → 나머지
```

**실무 해석:**
- KOSPI 1% 하락 → 삼성전자 0.7~0.8% 하락 (베타 효과)
- GDP 대비 시가총액 > 2.5 → 버블 신호

---

## 포트폴리오 최적화 진화

### Mean-Variance Frontier (Markowitz)

```python
# 최적 가중치
w = (Σ⁻¹ · a) / (a' · Σ⁻¹ · a)
```

**핵심 문제 (반드시 확인):**
- Asset 수 증가 → Σ⁻¹가 0에 수렴 → NaN 발생
- Cov가 1에 가까운 자산이 많을수록 Σ⁻¹ 계산 불가
- **해결 순서**: Eigenvalue → Determinant 확인 → 상관 높은 자산 제거

### Marcenko-Pastur 기반 노이즈 제거

랜덤 행렬 이론으로 공분산 행렬의 노이즈 eigenvalue를 분리:
```python
# q = T/N (관측치/자산수)
eMax = var * (1 + (1/q)**0.5)**2  # 노이즈 임계값
# eMax 이하 eigenvalue = 노이즈 → 제거 또는 교체
# Ledoit-Wolf shrinkage도 대안
```

### Hierarchical Risk Parity (HRP)

**언제 쓰는가:** Σ⁻¹ 계산이 불가능한 대규모 포트폴리오, 미래의 무한 자산 세계

```
HRP 원리:
  σᵢ² = σⱼ²이 같도록 → 변동성 균등화
  주식 변동성 10 : 채권 변동성 1 → 비율 1:10으로 배분
```

**MVF vs HRP 선택 기준:**
| | MVF | HRP |
|--|-----|-----|
| 수학적 최적성 | ✅ | ❌ |
| 대규모 자산 적용 | ❌ (Σ⁻¹ 불가) | ✅ |
| 직관성 | 낮음 | 높음 |
| 실무 활용 | 소규모 포트폴리오 | 대규모, ETF 구성 |

---

## ETF 분석 프레임

```
ETF = 여러 자산 바구니를 주식 형태로 거래 가능하게 쪼갠 상품

역사: Index ETF → Active ETF(알파 발굴) → 블록체인/RWA ETF(곧 등장)
```

**ETF 분석 순서:**
1. ETF 섹터 비율 확인 → 개별 종목 트렌드 사전 파악
2. 개별 종목 분석 전에 반드시 ETF 먼저
3. Top 5 섹터 파악 → 알파 발굴 포인트 설정
4. Kodex 구조 이해: 잘 조합된 바구니를 1/n으로 판매

**Alpha vs Beta:**
- Alpha(α): 인덱스 초과 수익 (발굴 목표)
- Beta(β): 시장 민감도 (관리 대상)

---

## 수치 계산 실패 시 디버깅 순서

```
1. Eigenvalue/Determinant 확인 (np.linalg.eig, np.linalg.det)
2. 상관관계 히트맵으로 군집 시각화
3. 상관 높은 자산 군집화 (Cluster Analysis)
4. 군집에서 대표 자산만 선택 (일부 제거)
5. HRP로 전환 고려
6. LedoitWolf shrinkage 적용
```

---

## 포트폴리오 구성 원칙

```
분산 크면 → 조금 담기 (But 리턴도 큼 = trade-off)
분산 작으면 → 많이 담기
같이 움직이는 자산 → 피하기 (상관관계 관리)

현실적 접근:
  1. Index ETF → 기본 베타 구축 (70-80%)
  2. 섹터 ETF → tactical allocation (~20%)
  3. 개별 자산 → 알파 추가
  4. RWA/코인 → 대안 자산 헷지
```

---

## HRP 핵심 수식 (de Prado 2016)

### 거리 행렬 변환

```
D(i,j) = √(0.5 × (1 − ρ(i,j)))

성질: 비음수, 대칭, 삼각부등식 만족 → 진정한 거리 지표
해석: D(i,j)가 클수록 두 자산이 더 다름 (비유사)
```

### 시스템 유사도 행렬 (D̄)

```
D̄(i,j) = √Σₖ (D(k,i) − D(k,j))²

의미: 자산 i와 j가 나머지 모든 자산들과 얼마나 유사한 상관 패턴을 갖는지
해석: D̄ 값이 낮을수록 두 자산이 시스템 전체와 동일한 방식으로 움직임

첫 번째 클러스터: U[1] = argmin D̄(i,j)
```

**D vs D̄ 구분:**
| | D 행렬 | D̄ 행렬 |
|--|--------|---------|
| 측정 대상 | 두 자산 간 직접 거리 | 포트폴리오 전체 내 시스템 유사도 |
| 낮은 값 의미 | 두 자산이 유사 | 두 자산이 나머지 자산들과 동일하게 반응 |
| 클러스터링 사용 | D → 덴드로그램 생성 | D̄ → 첫 클러스터 선택 |

---

## 공분산 행렬 수치 불안정 진단

### Condition Number (κ)

```
κ = λmax / λmin

κ가 클수록: 역행렬 계산 시 오류 증폭 → MVO 결과 불신뢰
κ ≈ 1: 이상적 (모든 고유값 동일)
κ > 1000: 수치 불안정 경고

진단 코드:
import numpy as np
eigenvalues = np.linalg.eigvalsh(cov_matrix)
kappa = eigenvalues.max() / eigenvalues.min()
```

### MVO 3대 실패 원인

```
1. 수치 불안정 (Numerical Instability)
   소규모 입력 변화 → 최적 포트폴리오 대폭 변동
   원인: κ가 큰 공분산 행렬의 역행렬 불안정

2. 과집중 (Excessive Concentration)
   최적화 결과 3~5개 자산에만 가중치 쏠림
   원인: 오류 최소화 대신 오류 증폭 자산 선택

3. 낮은 표본외 성과 (Poor Out-of-Sample)
   데이터 과적합 → 실전 성과 저조
   원인: 수익률 추정 불확실성에 과도한 의존
```

---

## 60/40 포트폴리오의 함정

```
60/40 포트폴리오 실제 리스크 분포:
  주식 변동성:  연 15-20%
  채권 변동성:  연 3-5%

→ 전체 리스크의 약 90%가 주식에서 발생 (금액 비중은 60%이지만)

2008 금융위기 시 이 함정으로 인한 대형 손실 발생
→ Risk Parity의 등장 배경
```

**Risk Parity 해법:**
```
역분산 가중치: wᵢ ∝ 1/σᵢ²

주식 σ=15%, 채권 σ=5% → 가중치 비율 1:9 (금액)
결과: 각 자산이 포트폴리오 리스크에 동일 기여
실적: AQR, Bridgewater 검증 전략
```

---

## HRP 성과 검증

```
de Prado (2016) Monte Carlo 시뮬레이션 결과:
  HRP vs CLA (Critical Line Algorithm)
  → HRP: CLA 대비 분산 72% 감소

이유:
  1. 공분산 역행렬 불필요 → 수치 오류 없음
  2. 클러스터 내 경쟁만 허용 → 오류 전파 차단
  3. 재귀적 이분법 → 자연스러운 리스크 분배
```

**scipy HRP 구현 핵심:**
```python
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform

# 1. 상관→거리 변환
dist = np.sqrt(0.5 * (1 - corr_matrix))

# 2. 계층적 클러스터링 (Single Linkage)
link = linkage(squareform(dist), method='single')

# 3. 준대각화 (Quasi-Diagonalization)
def get_quasi_diag(link):
    # 덴드로그램을 정렬하여 유사 자산을 인접하게 배치
    ...

# 4. 재귀적 이분법으로 가중치 배분
def get_rec_bipart(cov, sort_ix):
    # 각 클러스터 절반으로 재귀 분할, 역분산으로 배분
    ...
```

---

## Campbell Harvey (2015) 인용

> "100개 이상의 이상 현상(anomaly)이 발견된 건 통계적 유의성의 위기가 아니라 데이터 마이닝의 위기다"
> — Campbell Harvey, 2015, "… and the Cross-Section of Expected Returns"

**실무 적용:**
- 팩터 모델 구축 시 과거 데이터 이상 현상만으로 포트폴리오 설계 경계
- 경제학적 인과관계 없는 statistical fit은 표본외 성과 보장 안 함
