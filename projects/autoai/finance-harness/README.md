# Finance Harness Plugin v2.0.0

금융 분석 특화 Claude Code 플러그인. auth-system의 다중 에이전트 인프라를 금융 도메인에 적용.

## 빠른 시작

```bash
cp .env.example .env
# .env에 API 키 입력

# 종합 주식 분석
/analyze AAPL 30d

# 전략 백테스팅
/backtest "momentum factor with 20d lookback"

# 뉴스 리서치
/research "Fed interest rate decision 2026"

# 포트폴리오 검토
/portfolio review
```

## 에이전트 팀

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| orchestrator | Opus | 작업 분해 & 통합 |
| researcher | Sonnet + Gemini | 뉴스/문서 수집 |
| analyst | Sonnet | 재무/기술적 분석 |
| coder | Haiku + Codex | 팩터/백테스팅 코드 |
| risk-mgr | Opus | 리스크 평가 & 승인 |

## 디렉토리 구조

```
finance-harness/
├── .claude/
│   ├── agents/          # 5개 에이전트 YAML
│   ├── commands/        # /analyze /backtest /research /portfolio
│   └── hooks.json       # 브로커 안전장치
├── scripts/api-helpers/ # 데이터 수집 스크립트
├── skills/              # 방법론 & 규정 문서
└── outputs/             # 분석 결과 (gitignored)
```

## 스킬 파일

- `skills/econ-methodology.md` — LASSO, VIX 분해, 기간 분리 규칙
- `skills/financial-standards.md` — 리포트 형식, 인용 규칙
- `skills/risk-framework.md` — VaR/CVaR/MDD 임계값
- `skills/compliance-rules.md` — 법적 면책, 공시 요건

## 검증

```bash
# API 도구 확인
echo $PERPLEXITY_API_KEY | head -c 10
echo $FRED_API_KEY | head -c 5

# FRED 데이터 수집 테스트
./scripts/api-helpers/fred-fetch.sh GDP CPIAUCSL

# Perplexity 뉴스 수집 테스트
./scripts/api-helpers/perplexity-search.sh "Apple AAPL earnings 2026 Q1"
```

## 기반 아키텍처

auth-system (Claude-as-head + Codex/Gemini/Perplexity-as-hands) 패턴을 금융 도메인에 특화.
상세 설계: `../FINANCE_HARNESS_DESIGN.md`
