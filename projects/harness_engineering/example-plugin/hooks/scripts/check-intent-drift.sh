#!/bin/bash
# PreToolUse 훅 (Write | Edit): 의도 드리프트 방지
#
# INTENT.md 불변 원칙 기계적 검증:
#   1. Skills 파일을 AI가 직접 수정하려는가?
#   2. INTENT.md를 수정하려는가? (경고)
#   3. outputs/ 이외 경로에 분석 결과(데이터 파일)를 저장하려는가?
#   4. 어휘 레지스터에 없는 이름으로 새 agents/ 파일을 생성하려는가?

TOOL_INPUT="${CLAUDE_TOOL_INPUT:-{}}"

# file_path 추출
FILE_PATH=$(python3 -c "
import sys, json
try:
    d = json.loads('''$TOOL_INPUT''')
    print(d.get('file_path', ''))
except:
    print('')
" 2>/dev/null || echo "")

# file_path가 없으면 통과 (Edit의 경우 등)
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

VIOLATIONS=0

# ── 체크 1: Skills 파일 직접 수정 ──────────────────────────────────────
# 원칙: "Skills는 읽기 전용 — AI는 Skills 파일을 수정하지 않는다"
if echo "$FILE_PATH" | grep -qE "/skills/.*\.md$"; then
    echo ""
    echo "⛔ [INTENT 위반] Skills 파일은 AI가 수정할 수 없습니다."
    echo "   대상 파일: $FILE_PATH"
    echo "   위반 원칙: Invariant #6 — Skills는 읽기 전용"
    echo "   해결 방법: 사용자에게 수동 수정을 요청하거나, 새 Skills 파일 추가를 제안하라"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# ── 체크 2: INTENT.md 수정 시도 ─────────────────────────────────────────
# 경고만 (사용자가 의도적으로 수정할 수 있으므로 차단하지 않음)
if echo "$FILE_PATH" | grep -qE "INTENT\.md$"; then
    echo ""
    echo "⚠️  [INTENT 경고] INTENT.md 수정 시도가 감지되었습니다."
    echo "   이 파일은 명시적 승인 후에만 수정 가능합니다."
    echo "   수정 이유를 사용자에게 먼저 설명하고 확인을 받으십시오."
    # 차단하지 않음 — exit 0 유지
fi

# ── 체크 3: outputs/ 이외에 분석 결과 파일 저장 ─────────────────────────
# 원칙: "출력은 outputs/ 하위에만"
if echo "$FILE_PATH" | grep -qE "\.(json|csv|parquet|xlsx|docx|pdf|png|jpg|svg)$"; then
    if ! echo "$FILE_PATH" | grep -qE "(outputs/|/tmp/|\.claude/)"; then
        echo ""
        echo "⛔ [INTENT 위반] 분석 결과는 outputs/ 하위에만 저장할 수 있습니다."
        echo "   대상 파일: $FILE_PATH"
        echo "   위반 원칙: Invariant #4 — 출력은 outputs/ 하위에만"
        echo "   해결 방법: outputs/context/ 또는 outputs/reports/ 경로를 사용하라"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
fi

# ── 체크 4: 어휘 레지스터 미등록 에이전트 생성 ──────────────────────────
# 원칙: "도메인 어휘 우선 — 새 기능 전 어휘 레지스터 등록 먼저"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if echo "$FILE_PATH" | grep -qE "/agents/[^/]+\.md$"; then
    AGENT_NAME=$(basename "$FILE_PATH" .md)
    KNOWN_AGENTS="orchestrator|researcher|data-validator|macro-analyst|signal-interpreter|risk-mgr|quant-coder|report-writer"
    if ! echo "$AGENT_NAME" | grep -qE "^($KNOWN_AGENTS)$"; then
        if [ -n "$PLUGIN_ROOT" ] && [ -f "$PLUGIN_ROOT/INTENT.md" ]; then
            # INTENT.md에 해당 이름이 등록되어 있는지 확인
            if ! grep -q "$AGENT_NAME" "$PLUGIN_ROOT/INTENT.md" 2>/dev/null; then
                echo ""
                echo "⚠️  [INTENT 경고] 어휘 레지스터에 없는 새 에이전트 감지: $AGENT_NAME"
                echo "   INTENT.md 도메인 어휘 레지스터에 먼저 등록 후 생성하십시오."
                echo "   위반 원칙: Invariant #1 — 도메인 어휘 우선"
                # 경고만 (차단 아님 — 새 에이전트가 필요할 수 있으므로)
            fi
        fi
    fi
fi

# ── 결과 ─────────────────────────────────────────────────────────────────
if [ $VIOLATIONS -gt 0 ]; then
    echo ""
    echo "총 $VIOLATIONS 개의 INTENT 위반이 발견되었습니다."
    echo "작업을 중단하고 사용자에게 위반 내용을 보고하십시오."
    exit 1
fi

exit 0
