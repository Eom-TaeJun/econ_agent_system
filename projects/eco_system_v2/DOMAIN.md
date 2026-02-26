# eco_system_v2 — 도메인 & 명칭 참조

> 이 파일은 AI가 세션 시작 시 가장 먼저 읽어야 하는 참조 문서다.
> 코드 변경 시 이 파일도 함께 갱신한다.

---

## 1. 시스템 한 줄 정의

거시경제 지표 + 뉴스 리서치를 멀티에이전트로 분석해 **투자 신호(BULLISH / NEUTRAL / BEARISH)** 를 합의 도출하는 시스템.

---

## 2. 아키텍처 원칙

**경량 DDD + Hub-and-Spoke**

```
main.py
  └─ Orchestrator (Hub)
        ├─ AnalysisAgent (Spoke) ─→ Claude API
        └─ ResearchAgent  (Spoke) ─→ Perplexity API

계층 의존 방향:
  agents/ → domain/ + infrastructure/
  infrastructure/ → domain/
  domain/ → stdlib만 (외부 의존성 절대 금지)
```

**단일 프로젝트 내 계층 분리** — eimas처럼 기능별 별도 폴더로 쪼개지 않고, 하나의 프로젝트 안에서 `domain / agents / infrastructure` 계층으로 분리한다.

---

## 3. Ubiquitous Language (도메인 용어)

| 용어 | 타입 | 위치 | 정의 |
|------|------|------|------|
| `Signal` | Enum | `domain/signal.py` | 투자 방향: `BULLISH` / `NEUTRAL` / `BEARISH` |
| `EconomicSignal` | frozen dataclass (VO) | `domain/signal.py` | 에이전트 1개의 판단 결과. `(agent, signal, confidence, rationale, timestamp)` |
| `MarketData` | frozen dataclass (VO) | `domain/market_data.py` | 수집된 거시경제 스냅샷. `(vix_current, vix_30d_avg, spx_return_30d, fed_rate, collected_at)` |
| `ConsensusService` | Domain Service | `domain/consensus.py` | `EconomicSignal[]` → 다수결 합의 `EconomicSignal` 반환. 합의 로직은 **여기에만** 작성 |
| `EcoResult` | 결과 컨테이너 | `agents/orchestrator.py` | 파이프라인 최종 결과: `(date, consensus, agent_signals, market_data)` |
| `BaseAgent` | ABC | `agents/base.py` | 모든 에이전트 베이스. `execute()` 추상 메서드 + `run()` 재시도/타임아웃 래퍼 |
| `Orchestrator` | Hub | `agents/orchestrator.py` | 스포크 에이전트를 `asyncio.gather`로 병렬 실행 → `ConsensusService`로 합의 |
| `AnalysisAgent` | Spoke | `agents/analysis.py` | Claude 기반 정량 분석 에이전트 |
| `ResearchAgent` | Spoke | `agents/research.py` | Perplexity 기반 뉴스 리서치 에이전트 |
| `collect_market()` | 함수 | `infrastructure/collectors/yfinance_collector.py` | VIX + SPX 수집 → `MarketData` 반환 |
| `collect_fed_rate()` | 함수 | `infrastructure/collectors/fred_collector.py` | FRED에서 연방기금금리 수집 → `float` 반환 |

---

## 4. Value Object 필드 상세

### MarketData
| 필드 | 단위 | 설명 |
|------|------|------|
| `vix_current` | 지수 | 현재 VIX |
| `vix_30d_avg` | 지수 | VIX 30일(22거래일) 평균 |
| `spx_return_30d` | % | S&P500 30일 수익률 |
| `fed_rate` | % | FEDFUNDS (연방기금금리) |
| `collected_at` | ISO 8601 | 수집 시각 |

### EconomicSignal
| 필드 | 타입 | 설명 |
|------|------|------|
| `agent` | str | 판단 주체 (`"analysis"`, `"research"`, `"consensus"`) |
| `signal` | Signal | BULLISH / NEUTRAL / BEARISH |
| `confidence` | float 0~1 | 판단 신뢰도 |
| `rationale` | str | 판단 근거 (자연어) |
| `timestamp` | ISO 8601 | 판단 시각 |

---

## 5. job_assistant 연동 (포트폴리오 모드)

job_assistant(`~/projects/self/job_assistant/`)가 생성한 `*_analysis.json`을 주입해
기업 관점 분석 + 포트폴리오 마크다운을 생성할 수 있다.

```bash
# step 1: job_assistant로 기업 분석 (Analysis JSON 생성)
cd ~/projects/self/job_assistant
python main.py --company 웨이브릿지 --role "퀀트리서처"
# → data/outputs/웨이브릿지_퀀트리서처_2026-02-26_analysis.json

# step 2: eco_system_v2로 거시경제 분석 + 포트폴리오 리포트
cd ~/projects/eco_system_v2
python main.py --quick \
  --load-profile ../self/job_assistant/data/outputs/웨이브릿지_퀀트리서처_2026-02-26_analysis.json \
  --portfolio
# → outputs/portfolio/웨이브릿지_퀀트리서처_2026-02-26.md
```

**관련 파일:**

| 파일 | 역할 |
|------|------|
| `infrastructure/profile_loader.py` | Analysis JSON → `ProfileData` VO → context 문자열 |
| `infrastructure/persistence/portfolio_writer.py` | 분석 결과 + 프로필 → 마크다운 리포트 |

**기업 추가 방법:** job_assistant만 실행하면 된다. eco_system_v2 코드는 건드릴 필요 없다.

---

## 6. 실행 모드

| 모드 | 명령어 | 실행 에이전트 | 소요 시간 |
|------|--------|--------------|----------|
| quick | `python main.py --quick` | AnalysisAgent만 | ~30초 |
| full | `python main.py --full` | AnalysisAgent + ResearchAgent 병렬 | ~60초 |
| 포트폴리오 | `--load-profile PATH --portfolio` | 위와 동일 + 마크다운 리포트 생성 | 동일 |

```bash
# 추가 컨텍스트 삽입
python main.py --full --context "Fed pivot 가능성 높음"

# 저장 건너뜀
python main.py --quick --no-save
```

---

## 6. 합의 알고리즘

`ConsensusService.compute(signals)`:
1. 다수결로 대표 `Signal` 결정
2. 대표 신호에 동의한 에이전트들의 `confidence` 평균
3. 빈 리스트 → `NEUTRAL, confidence=0.0`

---

## 7. 필수 환경변수

| 변수 | 필수 여부 | 용도 |
|------|----------|------|
| `ANTHROPIC_API_KEY` | 항상 필수 | AnalysisAgent (Claude) |
| `PERPLEXITY_API_KEY` | full 모드만 | ResearchAgent |
| `FRED_API_KEY` | 선택 | 없으면 fed_rate=0.0 |
| `CLAUDE_MODEL` | 선택 | 기본값: `claude-sonnet-4-6` |
| `PERPLEXITY_MODEL` | 선택 | 기본값: `sonar` |

---

## 8. Anti-patterns (절대 금지)

| 금지 패턴 | 이유 |
|-----------|------|
| `domain/`에 `import anthropic / httpx / yfinance` | 도메인 순수성 파괴 |
| `phases/` 폴더 스타일 (수집+분석 혼재) | eco_system v1의 실패 패턴 |
| `core/schemas.py` 패턴 (AgentRequest/AgentResponse) | domain VO로 대체 |
| `BaseAgent` 상속 없이 Orchestrator에 에이전트 직접 등록 | 재시도/타임아웃 보장 불가 |
| 합의 로직을 Orchestrator에 작성 | 반드시 `domain/consensus.py`에만 |
| 기능별 별도 폴더 분리 (onchain_intelligence 등 스타일) | 이 시스템은 계층 분리로 해결 |

---

## 9. 신규 에이전트 추가 방법

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

`agents/orchestrator.py`의 `_get_spokes()`에 추가하면 끝.

---

## 10. 출력 형식

`outputs/eco_{date}_{id}.json`

```json
{
  "date": "2026-02-26",
  "consensus_signal": "BULLISH",
  "consensus_confidence": 0.75,
  "consensus_rationale": "BULLISH 합의 (2/2명 동의: analysis, research), 평균 신뢰도 75%",
  "agent_signals": [
    {"agent": "analysis", "signal": "BULLISH", "confidence": 0.8, "rationale": "...", "timestamp": "..."},
    {"agent": "research", "signal": "BULLISH", "confidence": 0.7, "rationale": "...", "timestamp": "..."}
  ],
  "market_data": {
    "vix_current": 18.5,
    "vix_30d_avg": 20.1,
    "spx_return_30d": 3.2,
    "fed_rate": 5.33,
    "collected_at": "..."
  }
}
```
