# Project Overview

eco_system_v2는 거시경제 신호(BULLISH/NEUTRAL/BEARISH)를 멀티에이전트로 분석하는 시스템.
아키텍처: 경량 DDD + Hub-and-Spoke. Orchestrator(Hub) → Research/Analysis Agents(Spokes).

---

# Build & Setup

```bash
pip install -r requirements.txt

# 필수 환경변수
export ANTHROPIC_API_KEY=sk-ant-...
export PERPLEXITY_API_KEY=pplx-...   # full 모드만
export FRED_API_KEY=...              # 선택 (없으면 fed_rate=0.0)
```

---

# Project Structure

```
eco_system_v2/
├── domain/          ← 순수 도메인 (stdlib만 허용)
│   ├── signal.py         Signal enum, EconomicSignal(frozen dataclass)
│   ├── market_data.py    MarketData(frozen dataclass)
│   └── consensus.py      ConsensusService.compute(signals) → EconomicSignal
├── agents/          ← Bounded Contexts
│   ├── base.py           BaseAgent(ABC): run() = retry + timeout 래퍼
│   ├── research.py       ResearchAgent: Perplexity → EconomicSignal
│   ├── analysis.py       AnalysisAgent: Claude → EconomicSignal
│   └── orchestrator.py   Orchestrator(Hub): gather + ConsensusService
├── infrastructure/
│   ├── collectors/       yfinance_collector.py, fred_collector.py
│   └── persistence/      json_writer.py
├── config.py        API 키, 모델명 (환경변수)
└── main.py          CLI: --quick / --full
```

---

# Ubiquitous Language

| 용어 | 정의 |
|------|------|
| `Signal` | BULLISH / NEUTRAL / BEARISH enum |
| `EconomicSignal` | 에이전트 1개의 판단 VO: (agent, signal, confidence, rationale) |
| `MarketData` | 수집된 시장 데이터 VO: (vix_current, vix_30d_avg, spx_return_30d, fed_rate) |
| `ConsensusService` | 다수결 + 평균 신뢰도로 EconomicSignal 목록을 하나로 합의 |
| `EcoResult` | 파이프라인 최종 결과: consensus + agent_signals + market_data |

---

# Key Patterns

**Hub-and-Spoke** (`agents/orchestrator.py`):
```python
results = await asyncio.gather(*[spoke.run(market_data) for spoke in spokes])
consensus = ConsensusService.compute(valid_results)
```

**BaseAgent 재시도**:
```python
async def run(self, market_data, context="") -> EconomicSignal:
    for attempt in range(self.max_retries):
        return await asyncio.wait_for(self.execute(...), timeout=self.timeout_sec)
```

**에이전트 추가 방법**:
1. `agents/base.py`의 `BaseAgent` 상속
2. `execute(market_data, context)` 구현 → `EconomicSignal` 반환
3. `Orchestrator.__init__`에서 spoke 목록에 추가

---

# Testing

```bash
# smoke test — AnalysisAgent만 실행, 30초 이내
python main.py --quick

# full test — Research + Analysis 병렬
python main.py --full

# 도메인 순수성 검증 (0건 확인)
grep -r "import yfinance\|import anthropic\|import httpx" domain/

# 출력 확인
cat outputs/eco_*.json | python -m json.tool
```

---

# Boundaries (엄격 준수)

- `domain/`에 외부 의존성 추가 절대 금지 (anthropic, httpx, yfinance, fredapi)
- 합의 로직은 반드시 `domain/consensus.py`에만 작성
- 새 에이전트는 반드시 `BaseAgent` 상속
