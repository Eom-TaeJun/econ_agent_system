# eco_system_v2 — Progress

> 세션 간 연속성을 위한 작업 상태 추적 문서.
> 작업 완료/시작/보류 시 이 문서를 갱신한다.

---

## 완료된 작업

| 단계 | 작업 | 완료일 | 비고 |
|------|------|--------|------|
| P0 | Harness 기반 구축 (.claude/ 전체) | 2026-03-16 | commands, agents, skills, hooks |
| P1 | Domain 확장 (7개 VO 추가) | 2026-03-16 | RegimeResult, RiskMetrics, ForecastResult, DebateResult, AnalysisReport |
| P2 | Quant 인프라 (regime + risk 서비스) | 2026-03-16 | GMM 3-State + MA crossover, VaR/CVaR/MDD |
| P3 | 에이전트 확장 (5개) + Orchestrator 3모드 | 2026-03-16 | Analysis, Research, Quant, Forecast, Debate |
| P4 | 리포트 생성 (MD/HTML) | 2026-03-16 | Claude API → AnalysisReport → 파일 출력 |
| — | 문서 동기화 | 2026-03-17 | AGENTS.md, DOMAIN.md, ARCHITECTURE.md, SKILL.md v2 |
| — | HARNESS_DIRECTION.md 갱신 + PROGRESS.md 추가 | 2026-03-17 | 현재 상태 반영 |
| **P6a** | **합의 알고리즘 강화** | **2026-03-18** | **단순 다수결 → 신뢰도 가중 투표 + ConsensusBreakdown** |
| **P6b** | **히스토리 추적 + 트렌드 비교** | **2026-03-18** | **outputs/ 이력 읽기 → TrendComparison (방향변화, 연속횟수, 에이전트별 변화)** |
| **P5a** | **LASSO 예측 모델** | **2026-03-18** | **SPX 20일 전방 수익률 예측 + QuantAgent 통합 + 주요 동인 투명 보고** |
| **P5b** | **포트폴리오 배분 추천** | **2026-03-18** | **레짐→기본배분 + 신호/리스크/LASSO 조정 + 조정 이력 투명 기록** |
| **P7** | **수집기 확장** | **2026-03-18** | **2Y국채, 유가, 구리, HYG 수집 + QuantAgent oil/copper/HYG 스코어링** |

---

## 구현 로드맵 (중요도 순)

| 순위 | 작업 | 영향 범위 | 상태 | 비고 |
|------|------|-----------|------|------|
| 1 | 합의 알고리즘 강화 | `domain/consensus.py` | **완료** | 가중투표, 마진, AgentContribution, ConsensusBreakdown |
| 2 | 히스토리 추적 + 트렌드 비교 | `infrastructure/persistence/` + `domain/` | **완료** | TrendSnapshot, TrendComparison, history_reader |
| 3 | LASSO 예측 모델 (P5) | `infrastructure/analysis/lasso_service.py` | **완료** | SPX 20일 전방 예측, QuantAgent 통합 |
| 4 | 포트폴리오 배분 추천 (P5) | `infrastructure/analysis/portfolio_service.py` | **완료** | 레짐+신호+리스크+LASSO → 배분 |
| 5 | 수집기 확장 (Credit Spread, Commodity) | `infrastructure/collectors/` + `agents/quant.py` | **완료** | 2Y국채, 유가, 구리, HYG + QuantAgent 스코어링 |

---

## 보류/미래 작업

| 작업 | 우선순위 | 비고 |
|------|---------|------|
| 실시간 스트리밍 | 낮음 | 복잡도 높음, 코어 아님 |
| 모의매매 | 낮음 | 운용 기능, 분석과 별개 |
| 백테스트 | 낮음 | 대규모 인프라 필요 |
| Multi-LLM 검증 | 낮음 | Debate로 대체 가능 |
| PDF export | 낮음 | MD/HTML로 충분 |
| Korea 특화 수집기 | 낮음 | 별도 vertical |

---

## 알려진 이슈

| 이슈 | 상태 | 비고 |
|------|------|------|
| yfinance DXY 티커 | 해결 | `DX-Y.NYB` → `DX=F` (달러 선물)로 변경 |
| Claude JSON 코드블록 래핑 | 해결 | `_parse_json()`에 코드블록 strip 추가 (4개 에이전트 + report generator) |
| report max_tokens 부족 | 해결 | 2048 → 4096으로 증가 |

---

## 다음 세션 참고

- P6a(합의) + P6b(히스토리) + P5a(LASSO) + P5b(배분) 완료 (2026-03-18).
- 로드맵 #1~#5 모두 완료. 기본 분석 파이프라인 완성.
