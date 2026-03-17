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

---

## 보류/미래 작업

| 단계 | 작업 | 우선순위 | 비고 |
|------|------|---------|------|
| P5 | LASSO 예측 모델 | 중 | `infrastructure/analysis/lasso_service.py` |
| P5 | 포트폴리오 최적화 (HRP) | 중 | `infrastructure/analysis/portfolio_service.py` |
| — | 실시간 스트리밍 | 낮음 | 복잡도 높음, 코어 아님 |
| — | 모의매매 | 낮음 | 운용 기능, 분석과 별개 |
| — | 백테스트 | 낮음 | 대규모 인프라 필요 |
| — | Multi-LLM 검증 | 낮음 | Debate로 대체 가능 |
| — | PDF export | 낮음 | MD/HTML로 충분 |
| — | Korea 특화 수집기 | 낮음 | 별도 vertical |

---

## 알려진 이슈

| 이슈 | 상태 | 비고 |
|------|------|------|
| yfinance DXY 티커 | 해결 | `DX-Y.NYB` → `DX=F` (달러 선물)로 변경 |
| Claude JSON 코드블록 래핑 | 해결 | `_parse_json()`에 코드블록 strip 추가 (4개 에이전트 + report generator) |
| report max_tokens 부족 | 해결 | 2048 → 4096으로 증가 |

---

## 다음 세션 참고

- 코드는 P0-P4 완료 상태. `python main.py --full` 실행 확인됨 (2026-03-16).
- 문서와 코드가 동기화된 상태 (2026-03-17).
- P5 (LASSO + 포트폴리오) 진행 시 `infrastructure/analysis/`에 추가. eimas `lib/lasso_model.py`, `lib/portfolio_optimizer.py` 참조.
