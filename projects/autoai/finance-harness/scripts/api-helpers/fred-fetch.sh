#!/bin/bash
# FRED (Federal Reserve Economic Data) 경제지표 수집 헬퍼
# 용도: GDP, CPI, 실업률, Fed 금리 등 거시경제 지표 조회
#
# 사용법:
#   ./scripts/api-helpers/fred-fetch.sh GDP
#   ./scripts/api-helpers/fred-fetch.sh GDP CPIAUCSL UNRATE FEDFUNDS
#
# 환경 변수:
#   FRED_API_KEY  (필수) - .env 파일 또는 환경에서 로드
#
# 주요 시리즈 ID:
#   GDP       - 실질 GDP (분기)
#   CPIAUCSL  - 소비자물가지수 (월)
#   UNRATE    - 실업률 (월)
#   FEDFUNDS  - Fed Funds Rate (월)
#   DGS10     - 10년 국채 수익률 (일)
#   VIXCLS    - VIX 공포지수 (일)
#   SP500     - S&P 500 지수 (일)

set -euo pipefail

SCRIPT_VERSION="2.0.0"
FRED_BASE_URL="https://api.stlouisfed.org/fred/series/observations"

# --- 환경 변수 로드 ---
if [[ -f ".env" ]]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | grep 'FRED' | xargs) 2>/dev/null || true
fi

# --- 인수 확인 ---
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 SERIES_ID [SERIES_ID ...]"
  echo "Example: $0 GDP CPIAUCSL UNRATE"
  echo ""
  echo "Common series IDs:"
  echo "  GDP       Real GDP (quarterly)"
  echo "  CPIAUCSL  Consumer Price Index (monthly)"
  echo "  UNRATE    Unemployment Rate (monthly)"
  echo "  FEDFUNDS  Federal Funds Rate (monthly)"
  echo "  DGS10     10-Year Treasury (daily)"
  echo "  VIXCLS    VIX Fear Index (daily)"
  exit 1
fi

# --- API 키 확인 ---
if [[ -z "${FRED_API_KEY:-}" ]]; then
  echo "ERROR: FRED_API_KEY not set."
  echo "  Option 1: export FRED_API_KEY=your_key"
  echo "  Option 2: Add FRED_API_KEY=your_key to .env file"
  echo "  Get key at: https://fred.stlouisfed.org/docs/api/api_key.html"
  exit 1
fi

echo "[fred-fetch v${SCRIPT_VERSION}] Fetching ${#} series: $*" >&2

# --- 각 시리즈 수집 ---
RESULTS="{"
FIRST=true

for SERIES_ID in "$@"; do
  echo "[fred-fetch] Fetching: ${SERIES_ID}" >&2

  RESPONSE=$(curl -s -w "\n%{http_code}" \
    "${FRED_BASE_URL}?series_id=${SERIES_ID}&api_key=${FRED_API_KEY}&file_type=json&limit=10&sort_order=desc")

  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  BODY=$(echo "$RESPONSE" | head -n -1)

  if [[ "$HTTP_CODE" != "200" ]]; then
    echo "WARNING: FRED API returned HTTP $HTTP_CODE for ${SERIES_ID}" >&2
    continue
  fi

  SERIES_JSON=$(echo "$BODY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
observations = data.get('observations', [])
result = []
for obs in observations:
    if obs.get('value') != '.':
        result.append({
            'date': obs['date'],
            'value': float(obs['value']),
            'series_id': '${SERIES_ID}'
        })
print(json.dumps(result))
" 2>/dev/null || echo "[]")

  if [[ "$FIRST" == "true" ]]; then
    FIRST=false
  else
    RESULTS+=","
  fi
  RESULTS+="\"${SERIES_ID}\": ${SERIES_JSON}"
done

RESULTS+="}"
echo "$RESULTS" | python3 -m json.tool
