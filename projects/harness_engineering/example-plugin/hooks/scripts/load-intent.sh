#!/bin/bash
# SessionStart 훅: INTENT.md를 세션 컨텍스트에 주입
# load-market-context.sh 보다 먼저 실행되어야 한다

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname $(dirname $(realpath $0)))}"
INTENT_FILE="$PLUGIN_ROOT/INTENT.md"

if [ -f "$INTENT_FILE" ]; then
    echo "=== 프로젝트 의도 로드 (INTENT.md) ==="
    echo ""
    cat "$INTENT_FILE"
    echo ""
    echo "======================================="
    echo "✅ 의도 드리프트 방지 활성 — 위 원칙을 이 세션 내내 유지하라"
else
    echo "⚠️  INTENT.md 없음 — 의도 드리프트 방지 비활성"
    echo "   ${PLUGIN_ROOT}/INTENT.md 파일이 필요합니다"
fi
