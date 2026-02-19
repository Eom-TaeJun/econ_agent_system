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
