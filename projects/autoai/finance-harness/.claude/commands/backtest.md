---
description: 알파팩터 자동 생성 및 백테스팅 (Self-Evolving Loop)
argument-hint: <strategy_description>
allowed-tools: Read, Write, Bash
---

다음 전략을 백테스팅하라: "$ARGUMENTS"

---

## Phase 1 — 팩터 설계 및 코드 생성 (finance-coder 에이전트)

finance-coder 에이전트를 사용하여:

1. 전략 수식화:
   - "$ARGUMENTS" 전략을 수학적으로 명확히 정의
   - 진입/청산 조건 명시
   - 필요 데이터 목록 작성

2. Codex를 통한 코드 생성:
   ```
   codex exec --full-auto "
   Task: Implement {STRATEGY_NAME} strategy for backtesting

   Strategy definition: {수식화된 전략}

   Requirements:
   - Data: yfinance (S&P 500 components or specified tickers)
   - Period: 2019-01-01 to 2024-12-31 (5 years)
   - Rebalancing: Monthly
   - Transaction costs: 0.1% per trade
   - Output metrics: Sharpe ratio, MDD, annualized return, IC, turnover
   - Save to: outputs/backtest_{DATE}.json and outputs/backtest_{DATE}.md
   "
   ```

3. Self-Evolving Loop (최대 3회 재시도):
   - 실패 시 오류 분석 후 코드 수정
   - 각 시도마다 다른 접근법 사용

---

## Phase 2 — 백테스트 실행 및 결과 분석

결과 필수 포함 항목:
- **샤프 비율**: (연간 수익률 - 무위험 수익률) / 연간 변동성
- **최대낙폭 (MDD)**: 고점 대비 최대 손실
- **연환산 수익률**: 기하평균 수익률 × 252
- **정보 계수 (IC)**: 팩터 신호와 수익률 간 상관계수
- **거래 비율 (Turnover)**: 월평균 포지션 교체율

---

## Phase 3 — 리스크 검토 (finance-risk-mgr 에이전트)

finance-risk-mgr 에이전트를 사용하여:
1. 백테스트 결과의 리스크 특성 분석
2. 실사용 가능 여부 판단 (과최적화 위험 포함)
3. 워크포워드 테스트 권고사항 제시

---

## 최종 저장

- 코드: `outputs/factor_{STRATEGY_NAME}_{DATE}.py`
- 결과: `outputs/backtest_{DATE}.json`
- 요약: `outputs/backtest_{DATE}.md`

---

**백테스트 면책:**
> 백테스팅 결과는 과거 데이터 기반 시뮬레이션입니다.
> 미래 실제 수익을 보장하지 않습니다.
> 거래 비용, 슬리피지, 유동성 제약은 완전히 반영되지 않을 수 있습니다.
