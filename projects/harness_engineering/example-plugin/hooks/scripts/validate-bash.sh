#!/bin/bash
# PreToolUse 훅: Bash 명령어 위험도 사전 검증

set -euo pipefail

input=$(cat)
command_str=$(echo "$input" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")

if [ -z "$command_str" ]; then
  exit 0
fi

# 위험 패턴 탐지
BLOCKED_PATTERNS=(
  "rm -rf"
  "DROP TABLE"
  "DELETE FROM"
  "> /etc/"
  "chmod 777"
  "curl.*\| bash"
  "wget.*\| bash"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
  if echo "$command_str" | grep -qi "$pattern"; then
    echo "{
      \"decision\": \"deny\",
      \"reason\": \"위험 패턴 감지: '$pattern' — 금융 분석 하니스는 이 명령을 허용하지 않습니다.\",
      \"systemMessage\": \"보안 정책에 의해 차단된 명령입니다. 다른 방법을 사용하세요.\"
    }" >&2
    exit 2
  fi
done

# 경고 패턴 (차단하지 않고 경고만)
WARNING_PATTERNS=("pip install" "npm install" "apt install")
for pattern in "${WARNING_PATTERNS[@]}"; do
  if echo "$command_str" | grep -qi "$pattern"; then
    echo "{
      \"systemMessage\": \"⚠️ 패키지 설치 명령이 감지되었습니다. 의도한 명령인지 확인하세요: $command_str\"
    }"
    exit 0
  fi
done

exit 0
