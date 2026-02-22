---
description: 거시경제 종합 분석 실행
argument-hint: [주제] (예: "현재 경기", "Fed 금리", "인플레이션")
allowed-tools: Read, Write, Bash
---

**분석 주제:** $ARGUMENTS

다음 파이프라인을 순서대로 실행하라.

---

**Step 0 — EIMAS 선행 컨텍스트 로드** (있으면 활용)
EIMAS 시스템이 이미 분석 결과를 보유하고 있을 수 있다. 먼저 확인하라:
```
mcp__finance-analysis-harness_eimas__eimas_status()
```
- API 또는 파일이 있으면: `get_latest_analysis(section="recommendation")`과 `get_regime()`으로 선행 레짐·추천 로드
- 없으면: Step 1부터 독립 수행

**Step 1 — 오케스트레이션 계획 수립**
orchestrator 에이전트를 사용해 요청을 분해하고 에이전트 실행 계획을 수립하라.
결과는 `outputs/context/orchestration_plan.json`에 저장된다.

**Step 2 — 뉴스·공시 수집**
researcher 에이전트를 사용해 분석 주제 관련 뉴스·공시·리서치를 수집하라.
`GOOGLE_API_KEY`가 있으면 `gemini-3.1-pro-preview` API로 대규모 문서를 처리한다.
결과는 `outputs/context/research_summary.json`에 저장된다.

**Step 3 — 데이터 수집**
분석 주제에 필요한 지표를 아래 우선순위로 수집하라:
- 거시: GDP, CPI, PCE, NFP, Fed Funds Rate, 10Y-2Y 스프레드
- 시장: S&P500, VIX, HY OAS, DXY
- 주제 관련 추가 지표

EIMAS에서 이미 레짐이 확인됐다면 해당 레짐에 집중되는 지표를 추가 수집.
데이터는 최소 3년, 가능하면 10년 이상 수집.

**Step 4 — 데이터 검증**
data-validator 에이전트를 사용해 수집한 데이터의 품질을 검증하라.
검증 실패 항목이 있으면 반드시 사용자에게 보고하고 계속할지 확인하라.

**Step 5 — 거시 분석**
macro-analyst 에이전트를 사용해 현재 레짐과 정책 경로를 분석하라.

**Step 6 — 시그널 해석**
signal-interpreter 에이전트를 사용해 주요 시그널의 일관성을 확인하라.
결과는 `outputs/context/signal_summary.json`에 저장된다.

**Step 7 — 리스크 평가**
risk-mgr 에이전트를 사용해 VaR, CVaR, 테일 리스크, 시나리오 분석을 수행하라.
결과는 `outputs/context/risk_assessment.json`에 저장된다.
리스크 등급이 CRITICAL이면 사용자에게 즉시 경보를 발령하라.

**Step 8 — 코드 분석 & 시각화** (필요 시)
다음 조건 중 하나라도 해당하면 quant-coder 에이전트를 실행하라:
- 포트폴리오 최적화 요청이 있을 때
- 이상 탐지 시각화가 필요할 때
- 상관관계 매트릭스 계산이 필요할 때
결과는 `outputs/context/chart_paths.json`에 저장된다.

**Step 9 — 리포트 생성**
report-writer 에이전트를 사용해 분석 결과를 `outputs/reports/analyze_YYYYMMDD.md`에 저장하라.
이전 단계의 context 파일을 모두 읽어 통합 리포트를 작성한다.

---

**에이전트 핸드오프 규칙:**
- 각 에이전트의 출력은 `outputs/context/` 에 JSON으로 저장
- 다음 에이전트는 시작 전 이전 에이전트의 JSON을 읽고 시작
- 스키마는 `outputs/context/SCHEMA.md` 참고

각 단계 완료 후 진행 상황을 보고하고, 다음 단계로 넘어가기 전에 에러가 없는지 확인하라.
