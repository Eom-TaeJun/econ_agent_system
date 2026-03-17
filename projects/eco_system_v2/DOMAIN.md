# eco_system_v2 — 도메인 & 명칭 참조

> 이 파일은 AI가 세션 시작 시 가장 먼저 읽어야 하는 참조 문서다.
> 코드 변경 시 이 파일도 함께 갱신한다.

---

## 1. 시스템 한 줄 정의

거시경제 지표 + 뉴스 리서치 + 정량 분석을 멀티에이전트로 분석해 **투자 신호(BULLISH / NEUTRAL / BEARISH)** 를 합의 도출하는 시스템.

---

## 2. 아키텍처 원칙

**경량 DDD + Hub-and-Spoke**

```
main.py
  └─ Orchestrator (Hub)
        ├─ AnalysisAgent  (Spoke) ─→ Claude API
        ├─ ResearchAgent  (Spoke) ─→ Perplexity API
        ├─ QuantAgent     (Spoke) ─→ 순수 계산
        ├─ ForecastAgent  (Spoke) ─→ Claude API
        └─ DebateAgent    (Spoke) ─→ Claude API (순차)

계층 의존 방향:
  agents/ → domain/ + infrastructure/
  infrastructure/ → domain/
  domain/ → stdlib만 (외부 의존성 절대 금지)
```

**단일 프로젝트 내 계층 분리** — eimas처럼 기능별 별도 폴더로 쪼개지 않고, 하나의 프로젝트 안에서 `domain / agents / infrastructure` 계층으로 분리한다.

---

## 3. Ubiquitous Language (도메인 용어)

### 핵심 VO / Enum

| 용어 | 타입 | 위치 | 정의 |
|------|------|------|------|
| `Signal` | Enum | `domain/signal.py` | 투자 방향: `BULLISH` / `NEUTRAL` / `BEARISH` |
| `EconomicSignal` | frozen DC (VO) | `domain/signal.py` | 에이전트 1개의 판단 결과 |
| `MarketData` | frozen DC (VO) | `domain/market_data.py` | 수집된 거시경제 스냅샷 |
| `MarketRegime` | Enum | `domain/regime.py` | 시장 레짐 5종 (Bull/Bear × Low/High Vol + Transition) |
| `TrendState` | Enum | `domain/regime.py` | 추세 상태 5종 (Strong Up ~ Strong Down) |
| `VolatilityState` | Enum | `domain/regime.py` | 변동성 상태 5종 (Very Low ~ Extreme) |
| `RegimeResult` | frozen DC (VO) | `domain/regime.py` | 레짐 탐지 결과 (GMM 확률, 기술 지표, 전환 확률 포함) |
| `RiskLevel` | Enum | `domain/risk.py` | 리스크 수준: LOW / MEDIUM / HIGH / EXTREME |
| `RiskMetrics` | frozen DC (VO) | `domain/risk.py` | 리스크 지표 (VaR, CVaR, MDD, 실현변동성) |
| `HorizonType` | Enum | `domain/forecast.py` | 전망 시계: SHORT / MEDIUM / LONG |
| `ForecastResult` | frozen DC (VO) | `domain/forecast.py` | 전망 결과 (동인, 리스크 요인 포함) |
| `LASSOForecast` | frozen DC (VO) | `domain/forecast.py` | LASSO 정량 예측 (전방 수익률, R², 주요 동인) |
| `DebateResult` | frozen DC (VO) | `domain/debate.py` | 토론 합의 결과 (도전, 종합 해석 포함) |
| `ReportSection` | frozen DC (VO) | `domain/report.py` | 리포트 섹션 |
| `AnalysisReport` | frozen DC (VO) | `domain/report.py` | 최종 분석 리포트 (to_markdown() 지원) |

### 자산 배분 VO

| 용어 | 타입 | 위치 | 정의 |
|------|------|------|------|
| `AssetClass` | Enum | `domain/allocation.py` | 자산 클래스: EQUITY / BOND / GOLD / CASH |
| `AllocationAdjustment` | frozen DC (VO) | `domain/allocation.py` | 배분 조정 기록 (출처, 변화량, 사유) |
| `AllocationResult` | frozen DC (VO) | `domain/allocation.py` | 배분 추천 결과 (비율, 전략명, 조정 이력, 설명) |

### 트렌드 추적 VO

| 용어 | 타입 | 위치 | 정의 |
|------|------|------|------|
| `Direction` | Enum | `domain/trend.py` | 신호 변화 방향: UPGRADED / DOWNGRADED / REVERSED / UNCHANGED |
| `SignalChange` | frozen DC (VO) | `domain/trend.py` | 에이전트 하나의 이전→현재 신호 변화 |
| `TrendSnapshot` | frozen DC (VO) | `domain/trend.py` | 과거 분석 하나의 스냅샷 |
| `TrendComparison` | frozen DC (VO) | `domain/trend.py` | 현재 vs 직전 비교 (방향변화, 연속횟수, 에이전트별 변화, 설명) |

### 합의 과정 VO

| 용어 | 타입 | 위치 | 정의 |
|------|------|------|------|
| `AgentContribution` | frozen DC (VO) | `domain/consensus.py` | 개별 에이전트의 합의 기여 (가중치, 동의 여부) |
| `ConsensusBreakdown` | frozen DC (VO) | `domain/consensus.py` | 합의 과정 분해: 가중 점수, 마진, 기여도, 설명 |

### 서비스 / 컨테이너

| 용어 | 타입 | 위치 | 정의 |
|------|------|------|------|
| `ConsensusService` | Domain Service | `domain/consensus.py` | 신뢰도 가중 투표 합의. 합의 로직은 **여기에만** 작성 |
| `EcoResult` | 결과 컨테이너 | `agents/orchestrator.py` | 파이프라인 최종 결과: consensus + signals + market_data + regime + risk + debate |
| `BaseAgent` | ABC | `agents/base.py` | 모든 에이전트 베이스. `execute()` 추상 + `run()` 재시도/타임아웃 |
| `Orchestrator` | Hub | `agents/orchestrator.py` | 스포크 에이전트를 실행 후 ConsensusService로 합의 도출 |

### 인프라

| 용어 | 위치 | 정의 |
|------|------|------|
| `collect_market()` | `infrastructure/collectors/yfinance_collector.py` | VIX + SPX → MarketData |
| `collect_extended_market()` | `infrastructure/collectors/yfinance_collector.py` | SPX/VIX 시계열 + 10Y/2Y Treasury + DXY + Gold + Oil + Copper + HYG |
| `collect_fed_rate()` | `infrastructure/collectors/fred_collector.py` | FRED → 연방기금금리 float |
| `detect_regime()` | `infrastructure/analysis/regime_service.py` | GMM 3-State + MA 크로스오버 → RegimeResult |
| `calculate_risk()` | `infrastructure/analysis/risk_service.py` | VIX + 가격 시리즈 → RiskMetrics |
| `generate_report()` | `infrastructure/report/generator.py` | EcoResult dict → Claude → AnalysisReport |
| `write_report()` | `infrastructure/report/writer.py` | AnalysisReport → MD/HTML 파일 출력 |
| `forecast_with_lasso()` | `infrastructure/analysis/lasso_service.py` | 가격+VIX 시계열 → LASSO 20일 전방 수익률 예측 |
| `recommend_allocation()` | `infrastructure/analysis/portfolio_service.py` | 합의+레짐+리스크+LASSO → 자산 클래스 배분 추천 |
| `load_history()` | `infrastructure/persistence/history_reader.py` | outputs/eco_*.json → TrendSnapshot 리스트 |
| `compare_with_history()` | `infrastructure/persistence/history_reader.py` | 현재 결과 vs 이력 → TrendComparison |

---

## 4. Value Object 필드 상세

### MarketData
| 필드 | 타입 | 단위 | 설명 |
|------|------|------|------|
| `vix_current` | float | 지수 | 현재 VIX |
| `vix_30d_avg` | float | 지수 | VIX 30일(22거래일) 평균 |
| `spx_return_30d` | float | % | S&P500 30일 수익률 |
| `fed_rate` | float | % | FEDFUNDS (연방기금금리) |
| `treasury_10y` | float | % | 10년 국채 수익률 |
| `treasury_2y` | float | % | 2년 국채 수익률 |
| `dxy_index` | float | 지수 | 달러 인덱스 |
| `gold_price` | float | USD | 금 가격 |
| `oil_price` | float | USD | WTI 원유 가격 |
| `copper_price` | float | USD/lb | 구리 가격 |
| `hyg_price` | float | USD | HYG ETF (하이일드 채권, 신용 위험 프록시) |
| `collected_at` | str | ISO 8601 | 수집 시각 |
| `yield_spread_10y_2y` | property | % | 10Y-2Y 스프레드 (역전 시 음수) |
| `yield_spread_10y_ffr` | property | % | 10Y-FFR 스프레드 |

### EconomicSignal
| 필드 | 타입 | 설명 |
|------|------|------|
| `agent` | str | 판단 주체 (`"analysis"`, `"research"`, `"quant"`, `"forecast"`, `"debate"`, `"consensus"`) |
| `signal` | Signal | BULLISH / NEUTRAL / BEARISH |
| `confidence` | float 0~1 | 판단 신뢰도 |
| `rationale` | str | 판단 근거 (자연어) |
| `timestamp` | str | ISO 8601 |

### RegimeResult
| 필드 | 타입 | 설명 |
|------|------|------|
| `regime` | MarketRegime | 현재 시장 레짐 |
| `confidence` | float 0~1 | 레짐 판단 신뢰도 |
| `trend_state` | TrendState | 추세 상태 |
| `volatility_state` | VolatilityState | 변동성 상태 |
| `description` | str | 레짐 해석 |
| `strategy` | str | 권장 전략 |
| `risk_appetite` | str | 리스크 선호도 |
| `prev_regime` | str | 이전 레짐 |
| `days_in_regime` | int | 현 레짐 유지 일수 |
| `gmm_probabilities` | tuple[tuple[str, float], ...] | GMM Bull/Neutral/Bear 확률 |
| `indicators` | tuple[tuple[str, float], ...] | 기술 지표 (RSI, momentum 등) |
| `transition_probs` | tuple[tuple[str, float], ...] | 레짐 전환 확률 |

> frozen DC에서 dict 대신 `tuple[tuple[str, float], ...]`을 사용하는 이유: dataclass(frozen=True)는 mutable 필드를 허용하지 않음. dict는 mutable이므로 immutable tuple로 대체.

### RiskMetrics
| 필드 | 타입 | 설명 |
|------|------|------|
| `risk_level` | RiskLevel | LOW / MEDIUM / HIGH / EXTREME |
| `vix_current` | float | 현재 VIX |
| `realized_vol_20d` | float | 20일 실현 변동성 (연환산 %) |
| `var_95` | float | 95% VaR (일간 %) |
| `cvar_95` | float | 95% CVaR (일간 %) |
| `max_drawdown` | float | 최대 낙폭 (%) |
| `description` | str | 리스크 해석 |

### ForecastResult
| 필드 | 타입 | 설명 |
|------|------|------|
| `horizon` | HorizonType | SHORT_TERM (≤30d) / MEDIUM_TERM (31-90d) / LONG_TERM (≥180d) |
| `signal` | Signal | 전망 방향 |
| `confidence` | float 0~1 | 전망 신뢰도 |
| `rationale` | str | 전망 근거 |
| `key_drivers` | str | 주요 동인 |
| `risks` | str | 리스크 요인 |

### DebateResult
| 필드 | 타입 | 설명 |
|------|------|------|
| `final_signal` | Signal | 토론 후 최종 판단 |
| `confidence` | float 0~1 | 판단 신뢰도 |
| `agreement_ratio` | float 0~1 | 원래 합의 동의도 |
| `challenges` | str | 합의에 대한 도전/반론 |
| `synthesis` | str | 종합 해석 |
| `agent_signals_summary` | str | 입력된 에이전트 신호 요약 |

### AnalysisReport
| 필드 | 타입 | 설명 |
|------|------|------|
| `title` | str | 리포트 제목 |
| `summary` | str | 핵심 요약 |
| `sections` | tuple[ReportSection, ...] | 섹션 목록 |
| `generated_at` | str | ISO 8601 |

---

## 5. 실행 모드

| 모드 | 명령어 | 에이전트 | 소요 시간 |
|------|--------|---------|----------|
| quick | `python main.py --quick` | Analysis | ~30초 |
| full | `python main.py --full` | Analysis + Research + Quant → Debate | ~90초 |
| forecast | `python main.py --forecast` | Analysis + Research + Quant + Forecast → Debate | ~120초 |
| +report | `--report` 플래그 추가 | 위 + Claude 리포트 생성 | +30초 |
| +portfolio | `--load-profile PATH --portfolio` | 위 + 기업 타겟 포트폴리오 리포트 | 동일 |

```bash
python main.py --full --context "Fed pivot 가능성 높음"
python main.py --forecast --report
python main.py --quick --no-save
```

---

## 6. 합의 알고리즘

`ConsensusService.compute(signals)` → `(EconomicSignal, ConsensusBreakdown)`:

1. **신뢰도 가중 투표**: 각 에이전트의 confidence가 투표 가중치
2. Signal별 가중 점수 합산 → 최고 점수 Signal 채택
3. **마진 계산**: (1위 점수 - 2위 점수) / 전체 점수 → 결정의 확실성
4. **최종 신뢰도**: 동의 에이전트 가중평균 × 마진 보정 계수
5. **ConsensusBreakdown**: 에이전트별 기여, 점수, 마진, 납득 가능한 설명 포함
6. 빈 리스트 → `NEUTRAL, confidence=0.0`

---

## 7. 필수 환경변수

| 변수 | 필수 여부 | 용도 |
|------|----------|------|
| `ANTHROPIC_API_KEY` | 항상 필수 | AnalysisAgent, ForecastAgent, DebateAgent, Report |
| `PERPLEXITY_API_KEY` | full/forecast | ResearchAgent |
| `FRED_API_KEY` | 선택 | 없으면 fed_rate=0.0 |
| `CLAUDE_MODEL` | 선택 | 기본값: `claude-sonnet-4-6` |
| `PERPLEXITY_MODEL` | 선택 | 기본값: `sonar` |

---

## 8. 출력 형식

`outputs/eco_{date}_{id}.json`

```json
{
  "date": "2026-03-17",
  "consensus_signal": "BULLISH",
  "consensus_confidence": 0.72,
  "consensus_rationale": "BULLISH 합의 (3/4명 동의: analysis, research, quant), 평균 신뢰도 72%",
  "agent_signals": [
    {"agent": "analysis", "signal": "BULLISH", "confidence": 0.8, "rationale": "..."},
    {"agent": "research", "signal": "BULLISH", "confidence": 0.7, "rationale": "..."},
    {"agent": "quant", "signal": "BULLISH", "confidence": 0.65, "rationale": "VIX 안정(15.2); SPX 30d +4.1%; ..."},
    {"agent": "debate", "signal": "NEUTRAL", "confidence": 0.6, "rationale": "..."}
  ],
  "market_data": {
    "vix_current": 15.2,
    "vix_30d_avg": 17.3,
    "spx_return_30d": 4.1,
    "fed_rate": 4.33,
    "treasury_10y": 4.28,
    "dxy_index": 103.5,
    "gold_price": 2980.0,
    "collected_at": "..."
  },
  "regime": {
    "regime": "Bull (Low Vol)",
    "confidence": 0.85,
    "trend_state": "Strong Uptrend",
    "volatility_state": "Low",
    "gmm_probabilities": {"Bull": 0.72, "Neutral": 0.18, "Bear": 0.10},
    "indicators": {"rsi": 62, "momentum_20d": 5.3},
    "transition_probs": {"Bull→Bull": 0.91, "Bull→Neutral": 0.07, "Bull→Bear": 0.02}
  },
  "risk_metrics": {
    "risk_level": "low",
    "vix_current": 15.2,
    "realized_vol_20d": 12.8,
    "var_95": -1.52,
    "cvar_95": -2.1,
    "max_drawdown": 3.8
  },
  "debate_summary": "..."
}
```

---

## 9. Anti-patterns (절대 금지)

| 금지 패턴 | 이유 |
|-----------|------|
| `domain/`에 `import anthropic / httpx / yfinance` | 도메인 순수성 파괴 |
| `phases/` 폴더 스타일 (수집+분석 혼재) | eco_system v1의 실패 패턴 |
| `core/schemas.py` 패턴 (AgentRequest/AgentResponse) | domain VO로 대체 |
| `BaseAgent` 상속 없이 Orchestrator에 에이전트 직접 등록 | 재시도/타임아웃 보장 불가 |
| 합의 로직을 Orchestrator에 작성 | 반드시 `domain/consensus.py`에만 |
| 기능별 별도 폴더 분리 (onchain_intelligence 등 스타일) | 이 시스템은 계층 분리로 해결 |
| QuantAgent에 LLM 호출 추가 | 결정적(deterministic) 보장 파괴 |

---

## 10. 신규 에이전트 추가 방법

```python
# agents/my_agent.py
from agents.base import BaseAgent
from domain.market_data import MarketData
from domain.signal import EconomicSignal, Signal

class MyAgent(BaseAgent):
    def __init__(self, ...):
        super().__init__("my_agent", max_retries=2, timeout_sec=45.0)

    async def execute(self, market_data: MarketData, context: str = "") -> EconomicSignal:
        # 핵심 로직
        return EconomicSignal(agent=self.name, signal=Signal.NEUTRAL, ...)
```

1. `BaseAgent` 상속 + `execute()` 구현
2. `agents/orchestrator.py`의 적절한 Phase에 배치
3. `AGENTS.md`에 등록
4. `DOMAIN.md`에 새 VO 있으면 추가
