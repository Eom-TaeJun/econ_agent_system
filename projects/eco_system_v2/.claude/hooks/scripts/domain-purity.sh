#!/bin/bash
# domain-purity.sh — domain/ 디렉토리에 외부 import 추가 방지
#
# PreToolUse hook: Edit/Write 시 domain/ 파일에
# anthropic, httpx, yfinance, pandas, numpy 등 외부 의존성 import를 차단.

TOOL_INPUT="$1"

# domain/ 파일 수정인지 확인
if echo "$TOOL_INPUT" | grep -q "domain/"; then
  # 외부 import 패턴 감지
  FORBIDDEN_IMPORTS="import anthropic|import httpx|import yfinance|import pandas|import numpy|import sklearn|from anthropic|from httpx|from yfinance|from pandas|from numpy|from sklearn"

  if echo "$TOOL_INPUT" | grep -qE "$FORBIDDEN_IMPORTS"; then
    echo "BLOCKED: domain/ 파일에 외부 라이브러리 import 금지!"
    echo "domain/ 레이어는 stdlib만 허용합니다."
    echo "외부 의존성은 infrastructure/ 또는 agents/ 에서 사용하세요."
    exit 1
  fi
fi

exit 0
