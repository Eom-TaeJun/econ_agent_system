# autoai — 경제 인텔리전스 프로젝트

## 사용 가능한 API 키

- `ANTHROPIC_API_KEY` — Claude
- `PERPLEXITY_API_KEY` — Perplexity
- `OPENAI_API_KEY` — OpenAI
- `GOOGLE_API_KEY` — Gemini

## 코딩 컨벤션

- Python 3.10+, type hints 필수
- 한글 주석 허용
- 경제학 용어는 영어 유지 (LASSO, Granger Causality, VIX 등)

## 프로젝트 구조

- `eimas/` — 메인 시스템, **여기서 작업** (고유 CLAUDE.md 있음)
- `market_anomaly_detector_v2.2/` — 레거시 참조용 (변경 금지)
- `econ_agent_system/` — 별도 시스템 참조용 (변경 금지)
