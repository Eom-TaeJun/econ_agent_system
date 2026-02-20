---
description: 포트폴리오 리뷰 및 리밸런싱 추천
argument-hint: [review|rebalance]
allowed-tools: Read, Write, Bash
---

포트폴리오 $ARGUMENTS 분석을 수행하라.

**사용법:**
- `/portfolio review` — 현재 포트폴리오 리스크 분석
- `/portfolio rebalance` — 최적 리밸런싱 제안

---

## Step 1 — 리스크 평가 (finance-risk-mgr 에이전트)

finance-risk-mgr 에이전트를 사용하여:

1. 현재 포지션 수집 (사용자에게 포지션 정보 요청)
2. VaR, CVaR, MDD 계산
3. 집중 리스크 체크 (포지션 > 5%, 섹터 > 30%)
4. 상관관계 행렬 분석 (>0.8 경고)
5. 리스크 등급 (1-5) 산정

---

## Step 2 — 성과 분석 (finance-analyst 에이전트)

finance-analyst 에이전트를 사용하여:

1. 섹터별 배분 현황
2. 최근 30일/90일/1년 성과 귀인 분석
3. 벤치마크 대비 Alpha/Beta 계산
4. `./scripts/api-helpers/fred-fetch.sh SP500 VIXCLS` 거시 맥락

---

## Step 3 — 리밸런싱 추천 (rebalance 모드)

`/portfolio rebalance` 실행 시:

1. 최적 포트폴리오 가중치 계산 (HRP 또는 Mean-Variance)
2. 리밸런싱 주문 목록 생성
3. **risk-mgr 승인 요청** (자동 실행 금지)
4. 거래 비용 추정

---

## 최종 출력

**저장:** `outputs/portfolio_review_{DATE}.md`

```
## 포트폴리오 리뷰 — {DATE}

### 현재 상태
| 종목 | 비중 | 30일 수익 | 섹터 |
|------|------|----------|------|
| ... |

### 리스크 지표
- VaR (95%): {value}%
- MDD: {value}%
- 평균 상관계수: {value}

### 경고 사항
{경고 목록 또는 "없음"}

### 리밸런싱 제안
{제안 목록}

### 리스크 등급: {1-5}/5

[DISCLAIMER] ...
```

**중요:** 실제 주문은 risk-mgr 승인 + 사용자 최종 확인 후에만 실행.
