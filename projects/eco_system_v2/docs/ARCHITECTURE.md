# eco_system_v2 — Architecture

> 에이전트 흐름, 실행 모드, 계층 경계, 인프라 서비스를 설명하는 구조 문서.
> 구조 변경 시 이 문서를 먼저 갱신한다.

---

## 1. 프로젝트 구조

```
eco_system_v2/
├── domain/                         ← 순수 도메인 (stdlib만)
│   ├── signal.py                      Signal(Enum), EconomicSignal(VO)
│   ├── market_data.py                 MarketData(VO)
│   ├── consensus.py                   ConsensusService (다수결 합의)
│   ├── regime.py                      MarketRegime(Enum), TrendState, VolatilityState, RegimeResult(VO)
│   ├── risk.py                        RiskLevel(Enum), RiskMetrics(VO)
│   ├── forecast.py                    HorizonType(Enum), ForecastResult(VO)
│   ├── debate.py                      DebateResult(VO)
│   └── report.py                      ReportSection(VO), AnalysisReport(VO)
│
├── agents/                         ← Bounded Contexts
│   ├── base.py                        BaseAgent(ABC): run()=retry+timeout
│   ├── analysis.py                    AnalysisAgent → Claude API
│   ├── research.py                    ResearchAgent → Perplexity API
│   ├── quant.py                       QuantAgent → 순수 계산 (LLM 없음)
│   ├── forecast.py                    ForecastAgent → Claude API
│   ├── debate.py                      DebateAgent → Claude API (순차)
│   └── orchestrator.py                Orchestrator(Hub) + EcoResult
│
├── infrastructure/
│   ├── collectors/                 ← 외부 데이터 수집
│   │   ├── yfinance_collector.py      collect_market() + collect_extended_market()
│   │   └── fred_collector.py          collect_fed_rate()
│   ├── analysis/                   ← 정량 분석 서비스
│   │   ├── regime_service.py          detect_regime() — GMM + MA crossover
│   │   └── risk_service.py            calculate_risk() — VaR/CVaR/MDD
│   ├── report/                     ← 리포트 생성
│   │   ├── generator.py               generate_report() — Claude API → AnalysisReport
│   │   └── writer.py                  write_report() — MD/HTML 출력
│   ├── persistence/                ← 저장
│   │   ├── json_writer.py             write() — EcoResult JSON
│   │   └── portfolio_writer.py        write_portfolio() — 기업 타겟 MD
│   └── profile_loader.py             load_profile() — job_assistant JSON → ProfileData
│
├── config.py                       API 키, 모델명, 경로 (환경변수)
├── main.py                         CLI: --quick / --full / --forecast / --report
├── outputs/                        결과 JSON + 리포트
│
├── CLAUDE.md                       Claude Code 설정 (빌드, 경로, 스타일)
├── AGENTS.md                       에이전트 패턴 참조
├── DOMAIN.md                       도메인 용어 참조
│
├── .claude/
│   ├── commands/                   /run, /check, /status
│   ├── agents/                     eco-runner, eco-analyst
│   ├── skills/                     domain-guide, analysis-standards
│   └── hooks/                      domain purity 검사
│
└── docs/
    ├── ARCHITECTURE.md             ← 이 문서
    ├── HARNESS_DIRECTION.md        harness 방향성
    └── CLAUDE_SESSION_BRIEF.md     세션 브리핑
```

---

## 2. 계층 경계

```
main.py → agents/ → domain/ + infrastructure/ → 외부 API
```

| 계층 | import 허용 | 외부 의존성 |
|------|------------|-----------|
| `domain/` | stdlib만 | **절대 금지** |
| `agents/` | domain + infrastructure | anthropic (lazy import) |
| `infrastructure/` | domain + 외부 | yfinance, httpx, fredapi, anthropic, sklearn |
| `main.py` | 전체 | config, argparse |

---

## 3. 데이터 흐름

### 전체 파이프라인 (full 모드)

```
[Phase 1: 수집]
  yfinance → MarketData + price_series + vix_series
  FRED     → fed_rate
  yfinance → treasury_10y, dxy_index, gold_price

        ↓

[Phase 2: 병렬 분석]
  AnalysisAgent(Claude)   ─→ EconomicSignal
  ResearchAgent(Perplexity) ─→ EconomicSignal
  QuantAgent(계산)         ─→ EconomicSignal
    ├─ detect_regime(prices, vix) → RegimeResult
    └─ calculate_risk(market, regime, prices) → RiskMetrics

        ↓

[Phase 3: 순차 토론]
  DebateAgent(Claude, context=Phase2 신호) ─→ EconomicSignal

        ↓

[Phase 4: 합의]
  ConsensusService.compute([모든 EconomicSignal])

        ↓

[Phase 5: 출력]
  EcoResult → JSON 저장
  (--report) → generate_report(Claude) → AnalysisReport → MD/HTML
```

---

## 4. 정량 분석 인프라

### 레짐 탐지 (`infrastructure/analysis/regime_service.py`)

**2-계층 분류**:
1. **GMM 3-State**: sklearn GaussianMixture(n_components=3)로 (Returns, VIX) 2D 공간에서 Bull/Neutral/Bear 확률 추정. sklearn 없으면 규칙 기반 폴백.
2. **MA 크로스오버**: 50일/200일 이동평균 관계 + VIX 절대 수준으로 5종 레짐 분류.

**부가 지표**: RSI-14 (Wilder smoothing), 20일 모멘텀, 52주 고점 거리, VIX 백분위

**전환 확률**: 최근 시계열에서 레짐 전환 빈도를 추정해 transition_probs로 반환.

### 리스크 계산 (`infrastructure/analysis/risk_service.py`)

**지표**: Historical VaR 95%, CVaR (Expected Shortfall), 20일 실현변동성(연환산), Max Drawdown

**리스크 수준 분류**: VIX 수준 + 레짐 + 수익률 곡선 스프레드(10Y - FFR)
- 수익률 곡선 역전(< -0.5%) → EXTREME으로 승격

---

## 5. 리포트 생성 경로

```
EcoResult.to_dict()
    ↓
generate_report(result_dict, api_key, model)
  → Claude API (max_tokens=4096)
  → JSON 파싱 → AnalysisReport(title, summary, sections)
    ↓
write_report(report, output_dir, fmt="md"|"html")
  → outputs/report_{date}.md
  → outputs/report_{date}.html
```

리포트 섹션 (Claude가 생성):
1. 시장 개요
2. 에이전트 분석 종합
3. 리스크 평가
4. 투자 전략
5. 향후 전망

---

## 6. Harness 자산

| 자산 | 경로 | 역할 |
|------|------|------|
| `/run` | `.claude/commands/run.md` | 파이프라인 실행 |
| `/check` | `.claude/commands/check.md` | 최신 output 요약 |
| `/status` | `.claude/commands/status.md` | 시스템 상태 확인 |
| eco-runner | `.claude/agents/eco-runner.md` | 파이프라인 실행 전담 |
| eco-analyst | `.claude/agents/eco-analyst.md` | 결과 해석 전담 |
| domain-guide | `.claude/skills/domain-guide/SKILL.md` | 도메인 모델 자동 주입 |
| analysis-standards | `.claude/skills/analysis-standards/SKILL.md` | 정량분석 방법론 자동 주입 |
| domain-purity hook | `.claude/hooks/` | domain/에 외부 import 방지 |

---

## 7. 변경 이력

| 날짜 | 변경 | 범위 |
|------|------|------|
| 2026-03-16 | P0 Harness 기반 구축 | .claude/ 전체 |
| 2026-03-16 | P1 Domain 확장 (7개 VO) | domain/ 전체 |
| 2026-03-16 | P2 Quant 인프라 (regime + risk) | infrastructure/analysis/ |
| 2026-03-16 | P3 에이전트 확장 (5개) + Orchestrator 3모드 | agents/ 전체 |
| 2026-03-16 | P4 리포트 생성 | infrastructure/report/ |
| 2026-03-17 | 문서 동기화 (AGENTS.md, DOMAIN.md, ARCHITECTURE.md) | docs/ |
