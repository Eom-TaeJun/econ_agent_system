# eco_system_v2 — 에이전트 & 실행 패턴 참조

> 코드 변경 시 이 파일도 함께 갱신한다.

---

## 1. 아키텍처: Hub-and-Spoke

```
main.py
  └─ Orchestrator (Hub)
        ├─ AnalysisAgent  (Spoke) ─→ Claude API
        ├─ ResearchAgent  (Spoke) ─→ Perplexity API
        ├─ QuantAgent     (Spoke) ─→ 순수 계산 (LLM 없음)
        ├─ ForecastAgent  (Spoke) ─→ Claude API
        └─ DebateAgent    (Spoke) ─→ Claude API (순차 — 다른 신호 입력 필요)
```

의존 방향:
```
agents/ → domain/ + infrastructure/
infrastructure/ → domain/
domain/ → stdlib만 (외부 의존성 절대 금지)
```

---

## 2. 에이전트 목록

| 에이전트 | 파일 | LLM | 역할 | max_retries | timeout |
|----------|------|-----|------|------------|---------|
| **AnalysisAgent** | `agents/analysis.py` | Claude | 거시경제 정량 분석 | 2 | 45s |
| **ResearchAgent** | `agents/research.py` | Perplexity | 뉴스 + 이벤트 리서치 | 2 | 30s |
| **QuantAgent** | `agents/quant.py` | **없음** | 레짐 + 리스크 → 결정적 신호 | 1 | 30s |
| **ForecastAgent** | `agents/forecast.py` | Claude | 1~3개월 포워드 전망 | 2 | 60s |
| **DebateAgent** | `agents/debate.py` | Claude | Devil's Advocate 합의 도전 | 2 | 60s |

### ADR

- **QuantAgent는 LLM 없이 순수 계산**: 객관적 정량 신호와 주관적 LLM 해석 분리. 빠르고, 저렴하고, 결정적(deterministic).
- **DebateAgent는 순차 실행**: 다른 에이전트 신호를 context로 받아야 하므로 Phase 2에서 실행.

---

## 3. 실행 모드

| 모드 | 명령어 | Phase 1 (병렬) | Phase 2 (순차) | 소요 |
|------|--------|---------------|---------------|------|
| quick | `--quick` | AnalysisAgent | — | ~30s |
| full | `--full` | Analysis + Research + Quant | Debate | ~90s |
| forecast | `--forecast` | Analysis + Research + Quant + Forecast | Debate | ~120s |

추가 플래그:
- `--report`: 실행 후 Claude로 MD/HTML 리포트 생성 (Phase 4)
- `--context "텍스트"`: 에이전트 프롬프트에 추가 컨텍스트 주입
- `--no-save`: JSON 저장 건너뜀
- `--load-profile PATH --portfolio`: job_assistant 연동 포트폴리오 리포트

---

## 4. Orchestrator 흐름

### quick 모드
```
AnalysisAgent → ConsensusService → EcoResult
```

### full 모드
```
Phase 1 (asyncio.gather):
  ├─ AnalysisAgent  → EconomicSignal
  ├─ ResearchAgent  → EconomicSignal
  └─ QuantAgent     → EconomicSignal
          ↓
Phase 2 (sequential):
  └─ DebateAgent(context=Phase1 신호 요약) → EconomicSignal
          ↓
ConsensusService.compute([모든 신호]) → EcoResult
```

### forecast 모드
```
Phase 1 (asyncio.gather):
  ├─ AnalysisAgent  → EconomicSignal
  ├─ ResearchAgent  → EconomicSignal
  ├─ QuantAgent     → EconomicSignal
  └─ ForecastAgent  → EconomicSignal
          ↓
Phase 2 (sequential):
  └─ DebateAgent(context=Phase1 신호 요약) → EconomicSignal
          ↓
ConsensusService.compute([모든 신호]) → EcoResult
```

---

## 5. EcoResult 구조

`agents/orchestrator.py`의 결과 컨테이너:

| 필드 | 타입 | 포함 조건 |
|------|------|----------|
| `consensus` | `EconomicSignal` | 항상 |
| `agent_signals` | `list[EconomicSignal]` | 항상 |
| `market_data` | `MarketData` | 항상 |
| `regime` | `RegimeResult \| None` | full/forecast (QuantAgent 실행 시) |
| `risk_metrics` | `RiskMetrics \| None` | full/forecast (QuantAgent 실행 시) |
| `debate_summary` | `str` | full/forecast (DebateAgent 성공 시) |

---

## 6. BaseAgent 패턴

```python
class BaseAgent(ABC):
    def __init__(self, name, max_retries=2, timeout_sec=30.0)

    @abstractmethod
    async def execute(self, market_data: MarketData, context: str = "") -> EconomicSignal

    async def run(self, market_data, context="") -> EconomicSignal:
        # 재시도 + asyncio.wait_for 타임아웃 래퍼
```

**에이전트 추가 방법**:
1. `agents/base.py`의 `BaseAgent` 상속
2. `execute(market_data, context)` 구현 → `EconomicSignal` 반환
3. `agents/orchestrator.py`에서 적절한 Phase에 배치
4. 이 문서(`AGENTS.md`)에 등록

---

## 7. 합의 알고리즘

`domain/consensus.py` — `ConsensusService.compute(signals)`:

1. 다수결로 대표 `Signal` 결정
2. 대표 신호에 동의한 에이전트들의 `confidence` 평균
3. 빈 리스트 → `NEUTRAL, confidence=0.0`

합의 로직은 **반드시 이 파일에만** 작성.

---

## 8. QuantAgent 신호 계산

LLM 없이 score(-1 ~ +1) 누적 → 신호 결정:

| 요소 | 점수 범위 | 기반 |
|------|----------|------|
| VIX 수준 | -0.5 ~ +0.3 | 16/22/30 임계값 |
| SPX 30d 수익률 | -0.2 ~ +0.2 | ±3% 기준 |
| 레짐 | -0.35 ~ +0.3 | MarketRegime enum별 |
| 리스크 수준 | -0.3 ~ +0.1 | RiskLevel enum별 |
| GMM 확률 | 연속 | (Bull% - Bear%) × 0.3 |
| 수익률 곡선 | -0.25 ~ +0.1 | 10Y - FFR 스프레드 |
| DXY | -0.1 ~ +0.1 | 95/105 기준 |
| RSI | -0.05 ~ +0.05 | 30/70 기준 |

score > 0.2 → BULLISH, score < -0.2 → BEARISH, 기타 → NEUTRAL

---

## 9. Anti-patterns (절대 금지)

- `BaseAgent` 상속 없이 Orchestrator에 에이전트 직접 등록
- 합의 로직을 Orchestrator에 작성 (반드시 `domain/consensus.py`)
- QuantAgent에 LLM 호출 추가
- DebateAgent를 병렬 Phase에 배치 (다른 신호가 입력으로 필요)
- `domain/`에 외부 의존성 import
