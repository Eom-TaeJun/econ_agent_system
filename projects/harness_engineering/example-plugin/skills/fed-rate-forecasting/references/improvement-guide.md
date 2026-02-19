# FedWatch Forecasting 분석 개선 방향성

## forecasting_20251213.py 피드백 및 개선 제안

**작성일**: 2025-12-14  
**대상 코드**: forecasting_20251213.py  
**분석 관점**: 거시경제학, 계량경제학, 예측(Forecasting)

---

## 1. 거시경제학(Macroeconomics) 관점 개선 방향

### 1.1 변수 선택의 이론적 기반 강화

**현재 문제점**:
- 변수 선택이 데이터 가용성에 의존하며 이론적 근거가 불명확함
- Treasury 변수를 동시성(simultaneity) 문제로 제외했으나, 이 자체가 중요한 정보 손실을 초래할 수 있음
- 일부 변수 간 경제적 메커니즘 연결이 불분명함

**개선 방향**:

1. **Taylor Rule 기반 변수 그룹화 도입**
   - Output Gap 대리변수: Industrial Production 성장률, Capacity Utilization, Employment Gap
   - Inflation Gap 대리변수: Breakeven Inflation, CPI/PCE Surprise (실제 - 예상), Commodity Index
   - Financial Conditions 지수: NFCI(National Financial Conditions Index), Credit Spread, Dollar Index
   
2. **글로벌 스필오버(Spillover) 변수 추가 고려**
   - 중국 경제지표: PMI, Credit Impulse, 위안화 환율
   - 유럽 금리 기대: ECB OIS(Overnight Index Swap) 커브
   - 글로벌 금융 스트레스 지수: VIX 외에 MOVE Index(채권 변동성) 추가
   - 이유: Fed는 "글로벌 금융 환경"을 명시적으로 언급하며 정책 결정에 고려

3. **정책 채널별 변수 분류**
   - 기대 채널(Expectations Channel): Breakeven, Survey 기반 인플레이션 기대
   - 신용 채널(Credit Channel): Baa Spread, High Yield Spread, 은행 대출 기준
   - 자산 가격 채널(Asset Price Channel): S&P500, Housing Index, Dollar
   - 통화량 채널: M2 성장률, 준비금 변화

---

### 1.2 비대칭적 반응(Asymmetric Response) 모델링

**현재 문제점**:
- 선형 모델이 Fed의 비대칭적 반응 함수를 포착하지 못함
- Fed는 경기 상승기와 하락기에 서로 다른 민감도로 반응함
- VIX Threshold 분석(Section 17)에서 비선형성 힌트가 있으나 체계적으로 모델링되지 않음

**개선 방향**:

1. **Regime-Switching Model 또는 Threshold Model 도입 검토**
   - 인플레이션 체제: 인플레이션 > 3% vs ≤ 3% 구간 분리 분석
   - 변동성 체제: VIX > 20 vs ≤ 20 구간 (이미 일부 수행)
   - 경기 사이클: 확장기 vs 수축기 (NBER 경기 기준일 활용)
   
2. **체계적 상호작용 효과 분석**
   - Dollar × Credit Spread: 달러 강세 시 신용 위험의 영향이 달라지는지
   - VIX × Inflation Expectation: 변동성 환경에서 인플레이션 기대의 영향
   - Equity Return × Credit Spread: 주식과 신용의 동조/이탈 패턴

3. **Fed Put의 비대칭성 정량화**
   - 주식 하락 시 vs 상승 시 Fed 반응의 차이
   - 신용 스프레드 확대 시 vs 축소 시 반응의 차이
   - 임계치(Threshold) 추정: 어느 수준에서 Fed가 "반응"하기 시작하는지

---

### 1.3 정책 커뮤니케이션 변수 통합

**현재 문제점**:
- Fed 발언, FOMC 성명서, Dot Plot 자체의 정보가 모델에 포함되지 않음
- 이벤트 더미(CPI_Released 등)만 포함되어 있어 정보의 질적 측면이 누락

**개선 방향**:

1. **텍스트 기반 변수 추가 검토**
   - Fed 성명서 감성 분석 점수 (Hawkish-Dovish Index)
   - Fed 위원 발언의 매파/비둘기 지수 (예: Bloomberg Fed Speak Index)
   - Dot Plot 중앙값과 시장 기대의 괴리(Gap)
   - Fed Chair 기자회견 톤 변화

2. **이벤트 더미 세분화**
   - FOMC 직전(D-1, D-2) vs 직후(D+1, D+2) 더미
   - 중요 연설(Jackson Hole, Congressional Testimony) 더미
   - SEP(Summary of Economic Projections) 발표 여부 더미
   - Dot Plot revision 방향 더미 (상향 vs 하향 vs 유지)

3. **서프라이즈 측정**
   - CPI Surprise = 실제 CPI - 컨센서스 예상
   - Employment Surprise = 실제 NFP - 컨센서스
   - GDP Surprise = 실제 GDP - 컨센서스

---

## 2. 계량경제학(Econometrics) 관점 개선 방향

### 2.1 내생성(Endogeneity) 문제 대응

**현재 문제점**:
- Treasury 변수를 동시성 문제로 제외했으나, 다른 금융변수들도 유사한 문제 존재
- 예: Dollar Index, Credit Spread도 Fed 기대에 영향을 받으면서 동시에 영향을 줌
- OLS/LASSO는 인과관계가 아닌 예측 관계만 제공

**개선 방향**:

1. **Lagged 변수의 체계적 활용**
   - 현재: Section 11에서 1기 Lagged 변수 테스트
   - 개선: 최적 래그 선택을 위한 정보 기준(AIC, BIC) 활용
   - 변수별 최적 래그가 다를 수 있음 (VIX는 즉각 반응, Credit Spread는 지연 반응)

2. **Granger 인과성 검정 추가**
   - 각 설명변수가 d_Exp_Rate를 Granger-cause하는지 검정
   - 양방향 인과관계 확인으로 진정한 "선행 지표" 식별

3. **도구변수(IV) 접근법 검토** (고급)
   - 외생적 충격(예: OPEC 결정에 따른 유가 변동)을 도구변수로 활용
   - 주의: 적절한 도구변수 찾기가 현실적으로 어려울 수 있음

---

### 2.2 시계열 특성 고려 강화

**현재 문제점**:
- ADF 검정으로 정상성 확인했으나, 추가적인 시계열 진단 부족
- 자기상관(Autocorrelation) 구조가 명시적으로 모델링되지 않음
- HAC 표준오차 사용으로 일부 보정했으나 근본 해결은 아님

**개선 방향**:

1. **시계열 진단 강화**
   - Ljung-Box 검정: 잔차의 자기상관 확인
   - ARCH 검정: 조건부 이분산성(Conditional Heteroskedasticity) 확인
   - 구조적 변화 검정: Bai-Perron 검정으로 다중 구조 변화점 탐지

2. **동적 모형 검토**
   - ARDL(Autoregressive Distributed Lag) 모형: 종속변수의 래그와 설명변수의 래그 동시 포함
   - VAR(Vector Autoregression): 변수들 간 동시적 상호작용 모델링
   - State-Space Model: 시변(time-varying) 계수 추정

3. **패널 데이터 특성 활용**
   - 현재: Meeting별 그룹화만 활용
   - 개선: Meeting Fixed Effects 또는 Random Effects 모형 검토
   - Clustered Standard Errors: Meeting 수준에서 클러스터링

---

### 2.3 모형 선택 및 정규화 개선

**현재 문제점**:
- LASSO만 사용하여 변수 선택
- Ridge와의 간단 비교만 수행
- 최적 λ 선택에 Time-Series CV 사용은 적절하나, 더 정교한 방법 존재

**개선 방향**:

1. **추가 정규화 방법 비교**
   - Elastic Net: LASSO와 Ridge의 조합으로 상관된 변수 그룹 처리에 유리
   - Adaptive LASSO: 일관성(Consistency) 개선
   - Group LASSO: 변수 그룹(Credit, FX, Equity 등) 단위로 선택

2. **교차검증 방법 다양화**
   - Blocked Time-Series CV: 시간적 의존성 더 강하게 반영
   - Rolling Window CV: 구조 변화에 더 민감하게 반응
   - Leave-One-Meeting-Out CV: Meeting 단위 예측 성능 평가

3. **모형 불확실성 반영**
   - Bayesian Model Averaging: 여러 모형의 가중 평균
   - Bootstrap 기반 변수 선택 안정성 평가
   - Confidence Set 구축: 선택된 변수들의 불확실성 정량화

---

### 2.4 구조적 변화 분석 강화

**현재 문제점**:
- Dot Plot 날짜(2024-12-18)를 사전적으로 지정하여 분석
- 데이터 기반 구조 변화점 탐지가 아님
- 단일 구조 변화점만 고려

**개선 방향**:

1. **데이터 기반 구조 변화점 탐지**
   - Bai-Perron 검정: 다중 구조 변화점 자동 탐지
   - CUSUM 검정: 누적합 기반 변화점 탐지
   - Rolling Regression: 시간에 따른 계수 변화 시각화

2. **다중 이벤트 분석**
   - 트럼프 당선(2024-11-05)
   - 12월 Dot Plot(2024-12-18)
   - 2025년 1월 FOMC(2025-01-29)
   - 각 이벤트 전후 구조 변화 비교

3. **시변 계수(Time-Varying Coefficient) 모형**
   - Kalman Filter 기반 상태공간 모형
   - Local Linear Regression
   - Rolling Window Regression (이미 일부 수행)

---

## 3. 예측(Forecasting) 관점 개선 방향

### 3.1 예측 평가 체계 강화

**현재 문제점**:
- MAE, RMSE 위주의 평가로 예측 분포의 질(Quality)은 미평가
- Mincer-Zarnowitz 검정으로 편향 확인했으나, 추가적인 예측 효율성 검정 부재
- Out-of-sample 예측 성능 평가가 부족

**개선 방향**:

1. **예측 평가 지표 다양화**
   - Direction Accuracy: 방향(상승/하락) 예측 정확도
   - Hit Ratio: 특정 임계치 내 적중률
   - Diebold-Mariano 검정: 모형 간 예측력 비교 통계 검정
   - MCS(Model Confidence Set): 통계적으로 동등한 모형들의 집합 구성

2. **예측 구간(Prediction Interval) 평가**
   - Coverage Probability: 실제값이 예측 구간에 포함된 비율
   - Interval Width: 예측 구간의 평균 폭
   - Winkler Score: 구간 예측의 종합 점수

3. **Forecast Combination**
   - 여러 모형의 예측 결합
   - 최적 가중치 추정 (Bates-Granger 방법)
   - 시간에 따른 가중치 변화

---

### 3.2 실시간 예측 성능 평가

**현재 문제점**:
- 전체 샘플로 모형 추정 후 예측 오차 계산
- 실제 실시간(Real-time) 예측 환경과 다름
- 데이터 빈티지(Vintage) 문제 미고려

**개선 방향**:

1. **진정한 Out-of-Sample 테스트**
   - Expanding Window: 과거 데이터만 사용하여 순차적 예측
   - Rolling Window: 고정 기간 사용하여 예측
   - Recursive Estimation: 각 시점에서 모형 재추정

2. **실시간 데이터 환경 시뮬레이션**
   - T-1일 데이터만 사용하여 T일 예측
   - 데이터 발표 지연(Publication Lag) 고려
   - 사후 수정(Revision) 전 데이터 사용

3. **Pseudo Out-of-Sample 실험**
   - 훈련/검증/테스트 분할
   - 시간 순서 유지 (미래 정보 누출 방지)
   - 복수의 테스트 기간으로 강건성 확인

---

### 3.3 확률적 예측(Probabilistic Forecasting)

**현재 문제점**:
- 점추정(Point Forecast)만 제공
- 예측 불확실성 정량화 부족
- 확률 분포 예측이 없음

**개선 방향**:

1. **밀도 예측(Density Forecast)**
   - Quantile Regression: 다양한 분위수 예측
   - 예: 10%, 25%, 50%, 75%, 90% 분위수
   - Fan Chart 시각화

2. **시나리오 분석**
   - 베이스라인 시나리오
   - 매파적 시나리오 (인플레이션 지속)
   - 비둘기파 시나리오 (경기 침체)
   - 각 시나리오별 확률 부여

3. **앙상블 예측**
   - 복수 모형의 예측 분포 결합
   - Bootstrap을 통한 예측 분포 추정
   - Bayesian 예측 분포

---

### 3.4 실용적 예측 지표 개발

**현재 문제점**:
- 분석 결과가 학술적이지만 실용적 활용 방안이 불명확
- 투자자가 직접 사용할 수 있는 지표 부재

**개선 방향**:

1. **Signal 기반 지표 개발**
   - "인하 모멘텀 지수": 주요 변수들의 가중 합으로 인하 가능성 점수화
   - "서프라이즈 위험 지수": 예상 외 금리 결정 가능성 측정
   - "컨센서스 이탈 지수": 시장 기대와 모형 예측의 괴리

2. **조건부 확률 제공**
   - "VIX > 25일 때 인하 확률"
   - "달러 1% 하락 시 기대금리 변화"
   - "CPI 서프라이즈 +0.1% 시 기대금리 반응"

3. **포트폴리오 함의**
   - 금리 기대 변화에 따른 자산군별 예상 수익률
   - 헤지 전략 제안
   - 리밸런싱 시그널

---

## 4. 코드 구조 및 재현성 개선

### 4.1 모듈화 및 재사용성

**현재 문제점**:
- 단일 스크립트에 모든 분석이 포함되어 있음
- 함수 재사용이 어려움
- 파라미터 하드코딩

**개선 방향**:

1. **모듈 분리**
   ```
   fedwatch_analysis/
   ├── data/
   │   ├── loader.py          # 데이터 로딩
   │   └── preprocessor.py    # 전처리
   ├── models/
   │   ├── lasso.py           # LASSO 관련
   │   ├── ols.py             # OLS/HAC
   │   └── diagnostics.py     # 진단
   ├── analysis/
   │   ├── horizon.py         # Horizon별 분석
   │   ├── subperiod.py       # 기간별 분석
   │   └── structural.py      # 구조 변화
   ├── visualization/
   │   └── plots.py           # 시각화
   └── config.py              # 설정
   ```

2. **설정 파일 분리**
   - HORIZON_BINS, EXCLUDE_PATTERNS 등을 config.py로 이동
   - 날짜, 파일 경로 등 하드코딩 제거
   - YAML 또는 JSON 설정 파일 활용

---

### 4.2 재현성(Reproducibility) 강화

**개선 방향**:

1. **버전 관리**
   - requirements.txt 또는 pyproject.toml로 의존성 명시
   - Random seed 고정 (현재 일부만 고정)
   - 데이터 버전 명시

2. **로깅 및 추적**
   - 분석 과정의 상세 로그 기록
   - 중간 결과 자동 저장
   - 실행 파라미터 기록

3. **문서화**
   - Docstring 추가
   - README 상세화
   - 분석 노트북(Jupyter) 버전 제공

---

## 5. 요약: 우선순위별 개선 권장사항

### 높은 우선순위 (즉시 개선 권장)

1. **Lagged 변수의 체계적 활용 및 최적 래그 선택**
2. **Out-of-Sample 예측 성능 평가 추가**
3. **다중 구조 변화점 탐지 (Bai-Perron)**
4. **예측 구간(Confidence Interval) 제공**

### 중간 우선순위 (후속 연구에서 개선)

5. **비선형 모형 (Threshold, Regime-Switching) 도입**
6. **Elastic Net 등 추가 정규화 방법 비교**
7. **텍스트 기반 Fed 커뮤니케이션 변수 추가**
8. **Granger 인과성 검정**

### 낮은 우선순위 (장기 개선 과제)

9. **도구변수 접근법**
10. **State-Space 시변 계수 모형**
11. **Bayesian Model Averaging**
12. **글로벌 스필오버 변수 추가**

---

## 6. 참고 문헌 제안

- Cieslak, A., & Vissing-Jorgensen, A. (2021). "The Economics of the Fed Put." *Review of Financial Studies*
- Gürkaynak, R., Sack, B., & Swanson, E. (2005). "Do Actions Speak Louder Than Words?" *International Journal of Central Banking*
- Nakamura, E., & Steinsson, J. (2018). "High-Frequency Identification of Monetary Non-Neutrality." *Quarterly Journal of Economics*
- Bauer, M., & Swanson, E. (2023). "A Reassessment of Monetary Policy Surprises." *NBER Working Paper*

---

**문서 작성 완료**
