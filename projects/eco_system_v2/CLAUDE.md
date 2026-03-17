# Quick Facts

**프로젝트**: eco_system_v2 — 거시경제 멀티에이전트 분석 시스템 (2026 DDD 아키텍처)
**언어**: Python 3.11+, asyncio
**핵심 도메인 용어**: Signal / MarketData / EconomicSignal / ConsensusService / RegimeResult / RiskMetrics

> 도메인 용어 전체 정의 → [`DOMAIN.md`](./DOMAIN.md) (세션 시작 시 우선 읽기)

---

# Build & Test

```bash
pip install -r requirements.txt

# smoke test (~30초)
python main.py --quick

# full run (~90초) — Analysis + Research + Quant → Debate
python main.py --full

# forecast run — full + ForecastAgent
python main.py --forecast

# full + 리포트 생성
python main.py --full --report

# 도메인 순수성 검증 (0건이어야 함)
grep -r "import yfinance\|import anthropic\|import httpx" domain/

# 문법 검증
python -m compileall domain/ agents/ infrastructure/

# 결과 확인
cat outputs/eco_*.json
```

필수 환경변수: `ANTHROPIC_API_KEY`, `PERPLEXITY_API_KEY` (full만), `FRED_API_KEY` (선택)

---

# Key Directories

| 경로 | 역할 |
|------|------|
| `domain/` | 순수 도메인: Signal, MarketData, RegimeResult, RiskMetrics, ForecastResult, DebateResult, AnalysisReport |
| `agents/` | Bounded Contexts: BaseAgent + Analysis/Research/Quant/Forecast/Debate/Orchestrator |
| `infrastructure/collectors/` | yfinance, FRED 데이터 수집 어댑터 |
| `infrastructure/analysis/` | 정량분석 서비스 (regime_service, risk_service) |
| `infrastructure/report/` | 리포트 생성 + MD/HTML 출력 |
| `infrastructure/persistence/` | JSON 저장 어댑터 |
| `config.py` | API 키, 모델명, 경로 (환경변수) |
| `main.py` | CLI 진입점: --quick / --full / --forecast / --report |
| `outputs/` | 결과 JSON + 리포트 |
| `.claude/` | harness: commands, agents, skills, hooks |

---

# Execution Modes

| 모드 | 에이전트 | 설명 |
|------|---------|------|
| `--quick` | Analysis | AnalysisAgent만 (~30s) |
| `--full` | Analysis + Research + Quant → Debate | 병렬+순차 (~90s) |
| `--forecast` | Analysis + Research + Quant + Forecast → Debate | full + 전망 |
| `--report` | (추가 플래그) | 실행 후 MD/HTML 리포트 생성 |

---

# Code Style

- 타입 힌트 필수 (`from __future__ import annotations`)
- 함수 50줄 이하
- 에이전트 추가 시 `agents/base.py`의 `BaseAgent` 상속 필수
- 합의 로직은 `domain/consensus.py`에만 작성
- QuantAgent는 LLM 없이 순수 계산 (결정적)

---

# Anti-patterns (절대 금지)

- `domain/`에 `import anthropic`, `import httpx`, `import yfinance` 추가 금지
- `phases/` 폴더 스타일 (수집+분석 혼재) 금지 — infrastructure/로 분리
- `core/schemas.py` 패턴 (AgentRequest/AgentResponse) 금지 — domain/*.py VO 사용
- `BaseAgent` 상속 없이 Orchestrator에 에이전트 직접 등록 금지
- eimas 파일 통째 복사 금지 — 알고리즘만 추출

---

# Boundaries

```
main.py → agents/ → domain/ + infrastructure/ → 외부 API
```

- `domain/`: stdlib만 허용
- `agents/`: domain + infrastructure import 허용
- `infrastructure/`: 외부 라이브러리 허용 (yfinance, httpx, fredapi, anthropic)
