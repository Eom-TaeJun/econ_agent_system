#!/bin/bash
# 주가 및 재무 데이터 수집 헬퍼 (FinnHub API)
# 용도: OHLCV 주가, 재무제표, 피어 기업 데이터 조회
#
# 사용법:
#   ./scripts/api-helpers/market-data.sh AAPL --type quote
#   ./scripts/api-helpers/market-data.sh AAPL --type financials
#   ./scripts/api-helpers/market-data.sh AAPL --type peers
#   ./scripts/api-helpers/market-data.sh AAPL --type profile
#
# 환경 변수:
#   FINNHUB_API_KEY  (필수) - .env 파일 또는 환경에서 로드

set -euo pipefail

SCRIPT_VERSION="2.0.0"
FINNHUB_BASE_URL="https://finnhub.io/api/v1"

# --- 환경 변수 로드 ---
if [[ -f ".env" ]]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | grep 'FINNHUB' | xargs) 2>/dev/null || true
fi

# --- 인수 파싱 ---
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <TICKER> [--type quote|financials|peers|profile]"
  echo "Example: $0 AAPL --type quote"
  echo "Example: $0 AAPL --type financials"
  exit 1
fi

TICKER="${1^^}"  # uppercase
DATA_TYPE="quote"

# Parse --type argument
shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --type)
      DATA_TYPE="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

# --- API 키 확인 ---
if [[ -z "${FINNHUB_API_KEY:-}" ]]; then
  echo "ERROR: FINNHUB_API_KEY not set."
  echo "  Option 1: export FINNHUB_API_KEY=your_key"
  echo "  Option 2: Add FINNHUB_API_KEY=your_key to .env file"
  echo "  Get key at: https://finnhub.io/dashboard"
  echo ""
  echo "  Fallback: pip install yfinance && python3 -c \"import yfinance as yf; print(yf.Ticker('${TICKER}').info)\""
  exit 1
fi

echo "[market-data v${SCRIPT_VERSION}] ${TICKER} / ${DATA_TYPE}" >&2

# --- API 호출 ---
case "$DATA_TYPE" in
  quote)
    ENDPOINT="${FINNHUB_BASE_URL}/quote?symbol=${TICKER}&token=${FINNHUB_API_KEY}"
    ;;
  financials)
    ENDPOINT="${FINNHUB_BASE_URL}/stock/metric?symbol=${TICKER}&metric=all&token=${FINNHUB_API_KEY}"
    ;;
  peers)
    ENDPOINT="${FINNHUB_BASE_URL}/stock/peers?symbol=${TICKER}&token=${FINNHUB_API_KEY}"
    ;;
  profile)
    ENDPOINT="${FINNHUB_BASE_URL}/stock/profile2?symbol=${TICKER}&token=${FINNHUB_API_KEY}"
    ;;
  *)
    echo "ERROR: Unknown data type '${DATA_TYPE}'. Use: quote|financials|peers|profile" >&2
    exit 1
    ;;
esac

RESPONSE=$(curl -s -w "\n%{http_code}" "$ENDPOINT")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" != "200" ]]; then
  echo "ERROR: FinnHub API returned HTTP $HTTP_CODE" >&2
  echo "$BODY" >&2
  exit 1
fi

# --- 결과 출력 (pretty-printed JSON) ---
echo "$BODY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
# Add metadata
result = {
    'ticker': '${TICKER}',
    'type': '${DATA_TYPE}',
    'data': data
}
print(json.dumps(result, indent=2))
"
