# 금융 × AI 직무 지도
> 작성일: 2026-02-24
> 목적: 지원 포지션 파악 및 소스 추가 전략 수립

---

## 1. 금융 직무 원형 분류

금융의 핵심 기능 6가지 — 모든 포지션은 여기서 파생된다.

| 기능 | 하는 일 | 대표 직함 |
|------|---------|----------|
| **리서치/분석** | 시장·기업·거시 분석 → 투자 근거 생산 | 애널리스트, 리서처 |
| **투자 결정** | 분석 결과 → 포트폴리오 구성 | 포트폴리오 매니저, 펀드매니저 |
| **트레이딩/실행** | 가격 발견, 포지션 실행 | 트레이더, 딜러 |
| **리스크 관리** | 손실 시나리오 모델링 → 한도 설정 | 리스크 매니저, 신용 분석가 |
| **의사결정 지원** | 경영진 전략 지원, FP&A | 전략기획, 재무기획 |
| **인프라/운영** | 결제·정산·시스템 | 운영, IT/시스템 |

---

## 2. AI 전환 후 직무 지도

### 2-A. 리서치/분석 → **AI-Augmented Research**

| 전통 역할 | AI 전환 후 | 핵심 변화 |
|----------|-----------|----------|
| 매크로 애널리스트 | Macro Data Scientist | 정성 보고서 → 정량 모델 + LLM 요약 |
| 크레딧 애널리스트 | Credit Risk ML Engineer | 재무제표 20개 항목 → 수천 개 피처 |
| 리서치 어시스턴트 | AI Research Analyst | 리포트 작성 → 프롬프트 + RAG 설계 |

**현재 요구 스킬:** Python · 통계 · NLP · 도메인(거시/신용) 지식

---

### 2-B. 투자 결정 → **Quantitative Portfolio Management**

| 전통 역할 | AI 전환 후 | 핵심 변화 |
|----------|-----------|----------|
| 포트폴리오 매니저 | Quant PM | 직관 → 알파 시그널 + AI 합성 |
| 펀드 리서처 | ML Researcher (Finance) | 기업 실사 → 대안 데이터 + 이상 탐지 |

**현재 요구 스킬:** 포트폴리오 이론 · ML · 시계열 · 백테스팅 엔지니어링

---

### 2-C. 트레이딩/실행 → **Algorithmic & AI Trading**

| 전통 역할 | AI 전환 후 | 핵심 변화 |
|----------|-----------|----------|
| 트레이더 | Algo Trader / ML Quant | 직관 매매 → 신호 기반 실행 |
| 퀀트 개발자 | ML Quant Engineer | 룰 기반 모델 → 강화학습 |

**현재 요구 스킬:** 저지연 엔지니어링 · 강화학습 · 마켓 마이크로스트럭처

---

### 2-D. 리스크 관리 → **AI Risk & Fraud Engineering** ⭐ 유망

| 전통 역할 | AI 전환 후 | 핵심 변화 |
|----------|-----------|----------|
| 시장 리스크 애널리스트 | Market Risk ML Engineer | VaR 모델 → CDE / Neural MDN |
| 신용 리스크 애널리스트 | Credit Risk Scientist | 점수모델 → 실시간 ML 파이프라인 |
| 사기 탐지 팀 | Fraud AI Engineer | 룰 기반 탐지 → 이상 탐지 모델 |
| 컴플라이언스 | RegTech AI Specialist | 수동 검토 → NLP + 자동화 |

**현재 요구 스킬:** 통계 · 이상 탐지 · 실시간 ML · 도메인 지식

---

### 2-E. 의사결정 지원 → **Decision Science** ⭐ 핵심 타겟

| 전통 역할 | AI 전환 후 | 핵심 변화 |
|----------|-----------|----------|
| FP&A 애널리스트 | Decision Scientist | 회계 집계 → 예측 모델 + 의사결정 루프 |
| 전략기획 | AI Strategy Analyst | SWOT → A/B 테스트 + 인과추론 |
| BI 분석가 | Data & Decision Scientist | 리포팅 → 실험 설계 + 자동화 |

**현재 요구 스킬:** 실험 설계 · 인과추론 · A/B 테스트 · 비즈니스 임팩트 측정

---

## 3. 한국 시장 특화 직군 (2025-2026)

### 핀테크 (토스, 카카오페이, 핀다 등)
| 직군 | 하는 일 |
|------|--------|
| Decision Scientist | 대출 심사 모델, 사용자 행동 분석, A/B 테스트 |
| ML Engineer | 추천 시스템, 사기 탐지, 신용 모델 서빙 |
| Data Scientist | 금융 데이터 분석, 고객 세분화, 상품 전략 |

### 전통 금융 AI 전환 (KB, 신한, 하나 등)
| 직군 | 하는 일 |
|------|--------|
| AI 개발자 (LLM) | 내부 AI 어시스턴트, 문서 분석, RAG 시스템 |
| MLOps 엔지니어 | AI 모델 서빙 인프라, GPU 최적화 |
| AI 리서처 | 자체 파운데이션 모델 연구 |

### 자산운용/헤지펀드
| 직군 | 하는 일 |
|------|--------|
| 퀀트 리서처 | 알파 시그널 개발, 백테스팅 |
| AI 포트폴리오 엔지니어 | HRP, 레짐 전환 모델 |
| 대안 데이터 분석가 | 위성·SNS·카드 데이터 → 투자 인사이트 |

---

## 4. 내 스킬 ↔ 직무 피팅 매트릭스

| 직무 | 필요 스킬 | 내가 가진 것 | 갭 |
|------|----------|------------|-----|
| **Decision Scientist** | 인과추론, A/B테스트, ML 모델링, 비즈니스 임팩트 | LASSO 논문, POSCO 문제정의, 경제학 | A/B 테스트 경험 부재 |
| **Credit Risk ML** | 신용 모델, ML, 실시간 파이프라인 | market_density (VaR/ES), forecast | 실제 신용 데이터 경험 없음 |
| **Quant Researcher** | 알파 시그널, 백테스팅, 수학적 엄밀성 | 논문(LASSO), regime_detection, EIMAS | 파이낸셜 수학 심화 |
| **AI Risk Engineer** | 이상 탐지, 실시간 ML, 리스크 도메인 | market_density (CDE/MDN), EIMAS | 프로덕션 배포 경험 |
| **Macro Data Scientist** | 거시경제, ML, 시계열 | 논문, EIMAS, forecast | **갭 가장 작음** |
| **ML Quant Engineer** | 저지연, 알고 트레이딩, 강화학습 | regime_detection, EIMAS | 강화학습, 저지연 시스템 |

---

## 5. 소스 추가 전략

### 현재 소스의 강점

| 소스 | 커버하는 직무 |
|------|------------|
| 논문 (LASSO + HAC + Chow Test) | Macro DS, Quant Researcher |
| market_density (CDE + VaR/ES) | AI Risk Engineer, Quant PM |
| POSCO 철강 | Decision Scientist (문제 정의력) |
| mlb-stats | ML Engineering 품질 증명 |
| forecast 파이프라인 | Macro DS, AI Research Analyst |

### 갭 → 추가해야 할 소스 후보

| 부족한 직무 역량 | 추가 방법 |
|----------------|----------|
| A/B 테스트 / 실험 설계 | stats19 프로젝트를 가설 검정 프레임으로 재서술 |
| 인과추론 | 논문의 Granger Causality / Chow Test → 인과추론으로 포지셔닝 |
| 실시간 ML 서빙 | EIMAS의 FastAPI 서빙 구조 언급 |
| 신용/대출 도메인 | 경제학 수강 과목 + 논문의 신용스프레드 분석 연결 |
| 대안 데이터 | tech-digest (Perplexity 자동 수집) → 대안 데이터 파이프라인으로 |

---

## 6. 포지션별 자소서 강조 포인트

### Decision Scientist (에이브랩스, 토스, 카카오페이류)
1. **문제 정의력**: POSCO — "비즈니스 개선안으로 재정의"
2. **검증 루프**: 논문 — "68회 롤링, 구조적 안정성 검증"
3. **도메인 + 기술 통합**: 경제학 + LASSO + 실제 데이터 적용
4. **실행력**: POSCO AI 프로젝트 — "프로토타입으로 팀 설득"

### AI Risk / Credit ML (KB AI, 신한, 핀테크)
1. **리스크 모델링**: market_density — CDE, VaR, ES 직접 구현
2. **검증 집착**: 백테스팅 8360% 버그 발견 에피소드
3. **통계 엄밀함**: 논문 — Newey-West HAC, Chow Test
4. **시스템 설계**: EIMAS 멀티에이전트 구조

### Macro Data Scientist (자산운용, IB 리서치)
1. **연준 정책 분석**: 논문 전체
2. **거시 모델링**: 50개 변수 → LASSO → 구조 변화 발견
3. **파이프라인 구축**: forecast/ — 자동화된 macro 데이터 수집·분석
4. **레짐 탐지**: regime_detection, EIMAS GMM 3-state

### Quant Researcher (자산운용, 퀀트 하우스)
1. **알파 연구 방법론**: 논문 — 롤링 윈도우, 변수 선택
2. **포트폴리오 이론**: EIMAS — HRP 포트폴리오 최적화 구현
3. **리스크 분해**: Bekaert VIX 분해, Lopez de Prado HRP
4. **백테스팅 엄밀함**: 버그 발견 → 무결성 체크 원칙
