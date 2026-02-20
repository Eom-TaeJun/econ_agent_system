---
description: 주식 종합 분석 (펀더멘털 + 기술적 + 뉴스 + 리스크)
argument-hint: <ticker> [period]
allowed-tools: Read, Write, Bash
---

$ARGUMENTS 주식에 대해 4단계 종합 분석을 수행하라.

**사전 설정:**
- TICKER: 첫 번째 인수 (예: AAPL)
- PERIOD: 두 번째 인수 (기본값: 30d)
- OUTPUT_FILE: outputs/{TICKER}_{DATE}.md
- DATE: 오늘 날짜 (YYYYMMDD 형식)

---

## Phase 1 — 뉴스 리서치 (finance-researcher 에이전트)

finance-researcher 에이전트를 사용하여:
1. `./scripts/api-helpers/perplexity-search.sh "{TICKER} stock news earnings guidance {YEAR}"` 실행
2. 최근 30일 뉴스, 공시, 애널리스트 리포트 수집
3. 감성 점수 (1-10) 산정
4. 주요 인용문과 출처 목록 제공

---

## Phase 2 — 재무 및 기술적 분석 (finance-analyst 에이전트)

finance-analyst 에이전트를 사용하여:
1. `./scripts/api-helpers/market-data.sh {TICKER} --type financials` 실행
2. `./scripts/api-helpers/market-data.sh {TICKER} --type quote` 실행
3. `./scripts/api-helpers/market-data.sh {TICKER} --type peers` 실행
4. `./scripts/api-helpers/fred-fetch.sh FEDFUNDS SP500 VIXCLS` 실행
5. 계산:
   - 밸류에이션: P/E, EV/EBITDA, PBR, ROE
   - 기술적 분석: RSI(14일), MACD(12/26/9), 52주 고저 대비 위치
   - DCF 내재가치 (WACC 10%, g 3% 기본값)
   - 피어 비교 (최소 3개 기업)

---

## Phase 3 — 리스크 평가 (finance-risk-mgr 에이전트)

finance-risk-mgr 에이전트를 사용하여:
1. VaR (95%, 99%) 계산
2. MDD 계산
3. 집중도 리스크 체크
4. 리스크 등급 (1-5) 산정
5. 조건부 투자 의견 (Bull/Bear case 각 3개)

---

## Phase 4 — 최종 리포트 통합

financial-standards 스킬 기준에 따라 리포트 작성:

1. Executive Summary (3줄)
2. 핵심 재무 지표 테이블
3. 밸류에이션 분석 (DCF + 피어)
4. 기술적 분석 (RSI, MACD, 52주 위치)
5. 뉴스 감성 요약 (Phase 1 결과)
6. 리스크 요인 (Phase 3 결과)
7. 투자 의견 (Buy/Hold/Sell + 목표가)
8. 면책 문구 (compliance-rules 스킬)

**저장:** outputs/{TICKER}_{DATE}.md

---

**중요:**
- 모든 수치에 출처와 날짜 명시
- 투자 의견은 반드시 리스크 요인과 함께 제시
- 면책 고지 포함 필수
