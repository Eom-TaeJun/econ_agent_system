#!/bin/bash
# SessionStart 훅: 프로젝트 컨텍스트와 환경변수 로드

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CONFIG_FILE="$PROJECT_DIR/.finance-config.json"

echo "=== Finance Analysis Harness 초기화 ==="

# 프로젝트 설정 파일 로드
if [ -f "$CONFIG_FILE" ]; then
  DOMAIN=$(jq -r '.domain // "general"' "$CONFIG_FILE" 2>/dev/null || echo "general")
  BASE_CURRENCY=$(jq -r '.base_currency // "USD"' "$CONFIG_FILE" 2>/dev/null || echo "USD")
  OUTPUT_DIR=$(jq -r '.output_dir // "outputs"' "$CONFIG_FILE" 2>/dev/null || echo "outputs")

  echo "export FINANCE_DOMAIN=$DOMAIN" >> "$CLAUDE_ENV_FILE"
  echo "export BASE_CURRENCY=$BASE_CURRENCY" >> "$CLAUDE_ENV_FILE"
  echo "export OUTPUT_DIR=$OUTPUT_DIR" >> "$CLAUDE_ENV_FILE"
  echo "프로젝트 설정 로드: domain=$DOMAIN, currency=$BASE_CURRENCY"
else
  echo "export FINANCE_DOMAIN=general" >> "$CLAUDE_ENV_FILE"
  echo "export BASE_CURRENCY=USD" >> "$CLAUDE_ENV_FILE"
  echo "export OUTPUT_DIR=outputs" >> "$CLAUDE_ENV_FILE"
  echo "기본 설정 사용 (설정 파일 없음)"
fi

# outputs/ 디렉토리 생성
mkdir -p "$PROJECT_DIR/outputs/charts" 2>/dev/null || true

# API 키 존재 여부 확인 (값은 노출하지 않음)
echo ""
echo "=== API 키 상태 ==="
[ -n "${FRED_API_KEY:-}" ] && echo "✅ FRED_API_KEY 설정됨" || echo "⚠️  FRED_API_KEY 미설정 (FRED 데이터 제한됨)"
[ -n "${OPENAI_API_KEY:-}" ] && echo "✅ OPENAI_API_KEY 설정됨" || echo "⚠️  OPENAI_API_KEY 미설정"
[ -n "${ANTHROPIC_API_KEY:-}" ] && echo "✅ ANTHROPIC_API_KEY 설정됨" || echo "⚠️  ANTHROPIC_API_KEY 미설정"
[ -n "${BOK_API_KEY:-}" ] && echo "✅ BOK_API_KEY 설정됨 (한국은행 데이터 사용 가능)" || echo "ℹ️  BOK_API_KEY 미설정 (한국 데이터 제한됨)"

echo ""
echo "✅ Finance Analysis Harness 초기화 완료"
