#!/bin/bash
# Perplexity API 금융 리서치 헬퍼
# 용도: 최신 금융 뉴스, 기업 공시, 시장 동향 조회
#
# 사용법:
#   ./scripts/api-helpers/perplexity-search.sh "Apple AAPL earnings Q1 2026"
#   ./scripts/api-helpers/perplexity-search.sh "Fed interest rate decision impact"
#   PERPLEXITY_MODEL=sonar ./scripts/api-helpers/perplexity-search.sh "query"
#
# 환경 변수:
#   PERPLEXITY_API_KEY  (필수) - .env 파일 또는 환경에서 로드
#   PERPLEXITY_MODEL    (선택) - 기본값: sonar

set -euo pipefail

SCRIPT_VERSION="2.0.0"

# --- 환경 변수 로드 ---
if [[ -f ".env" ]]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | grep 'PERPLEXITY' | xargs) 2>/dev/null || true
fi

# --- 인수 확인 ---
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"your financial research query\""
  echo "Example: $0 \"Apple AAPL earnings Q1 2026 guidance\""
  exit 1
fi

QUERY="$1"
MODEL="${PERPLEXITY_MODEL:-sonar}"

# --- API 키 확인 ---
if [[ -z "${PERPLEXITY_API_KEY:-}" ]]; then
  echo "ERROR: PERPLEXITY_API_KEY not set."
  echo "  Option 1: export PERPLEXITY_API_KEY=pplx-xxx"
  echo "  Option 2: Add PERPLEXITY_API_KEY=pplx-xxx to .env file"
  echo "  Get key at: https://www.perplexity.ai/settings/api"
  exit 1
fi

# --- API 호출 ---
echo "[perplexity-search v${SCRIPT_VERSION}] Model: ${MODEL}" >&2
echo "[perplexity-search] Query: ${QUERY}" >&2

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "https://api.perplexity.ai/chat/completions" \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"${MODEL}\",
    \"messages\": [
      {
        \"role\": \"system\",
        \"content\": \"You are a financial research assistant. Provide concise, accurate, and up-to-date financial information with citations. Include sentiment analysis (bullish/bearish/neutral) and key metrics when relevant. Always cite sources.\"
      },
      {
        \"role\": \"user\",
        \"content\": $(echo "$QUERY" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))')
      }
    ],
    \"return_citations\": true,
    \"return_images\": false
  }")

# --- 응답 처리 ---
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" != "200" ]]; then
  echo "ERROR: Perplexity API returned HTTP $HTTP_CODE" >&2
  echo "$BODY" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("error",{}).get("message","Unknown error"))' 2>/dev/null || echo "$BODY" >&2
  exit 1
fi

# --- 결과 출력 ---
echo "$BODY" | python3 -c '
import json, sys

data = json.load(sys.stdin)
content = data["choices"][0]["message"]["content"]
print(content)

# 인용 출력
citations = data.get("citations", [])
if citations:
    print("\n--- Sources ---")
    for i, url in enumerate(citations, 1):
        print(f"[{i}] {url}")
'
