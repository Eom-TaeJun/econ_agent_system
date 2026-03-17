---
description: "eco_system_v2 시스템 상태 확인. 환경변수, 의존성, 도메인 순수성을 점검한다."
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# /status — 시스템 상태 확인

## 점검 항목

1. **환경변수**: ANTHROPIC_API_KEY, PERPLEXITY_API_KEY, FRED_API_KEY 존재 여부
2. **의존성**: `python -c "import anthropic; import httpx; import yfinance"` 확인
3. **도메인 순수성**: `grep -r "import yfinance\|import anthropic\|import httpx" domain/` → 0건
4. **문법 검증**: `python -m compileall domain/ agents/ infrastructure/`
5. **최근 실행**: `outputs/` 내 최신 파일 날짜

## 출력

각 항목별 OK/WARN/FAIL 상태를 보고한다.
