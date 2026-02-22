#!/bin/bash
# PostToolUse 훅 (Write): 출력 적합성 검증 (Guardrails AI 패턴)
#
# outputs/context/*.json 파일이 쓰여질 때, 도메인 스키마에 맞는지 검증한다.
# 검증 실패 시 AI가 자동으로 재작성하도록 블록하고 이유를 반환한다.
#
# 참조: Guardrails AI의 on_fail="reask" 패턴
#       크로스-에이전트 도메인 어휘 일관성 보장

TOOL_INPUT="${CLAUDE_TOOL_INPUT:-{}}"

FILE_PATH=$(python3 -c "
import sys, json
try:
    d = json.loads('''$TOOL_INPUT''')
    print(d.get('file_path', ''))
except:
    print('')
" 2>/dev/null || echo "")

# outputs/context/ 하위 JSON만 검증
if ! echo "$FILE_PATH" | grep -qE "outputs/context/.*\.json$"; then
    exit 0
fi

if [ ! -f "$FILE_PATH" ]; then
    exit 0
fi

FILENAME=$(basename "$FILE_PATH")
VIOLATIONS=0

# ── 공통 유틸 ────────────────────────────────────────────────────────────────
json_get() {
    python3 -c "
import json, sys
try:
    d = json.load(open('$FILE_PATH'))
    val = d
    for k in '$1'.split('.'):
        val = val[k]
    print(val)
except:
    print('')
" 2>/dev/null
}

field_exists() {
    python3 -c "
import json, sys
try:
    d = json.load(open('$FILE_PATH'))
    val = d
    for k in '$1'.split('.'):
        val = val[k]
    print('yes')
except:
    print('no')
" 2>/dev/null
}

# ── 스키마 검증 ───────────────────────────────────────────────────────────────

case "$FILENAME" in

  regime_snapshot.json)
    REGIME=$(json_get "regime")
    CONFIDENCE=$(json_get "confidence")
    VALID_REGIMES="Goldilocks Overheating Stagflation Recession"

    if ! echo "$VALID_REGIMES" | grep -qw "$REGIME"; then
      echo ""
      echo "⛔ [CONFORMANCE] regime_snapshot.json 검증 실패"
      echo "   필드: regime = \"$REGIME\""
      echo "   허용값: Goldilocks | Overheating | Stagflation | Recession"
      echo "   조치: 도메인 어휘 레지스터에 정의된 값 중 하나로 재작성하라"
      VIOLATIONS=$((VIOLATIONS + 1))
    fi

    if [ -n "$CONFIDENCE" ] && [ "$CONFIDENCE" != "" ]; then
      python3 -c "
c = float('$CONFIDENCE')
if not (0.0 <= c <= 1.0):
    print('OUT_OF_RANGE')
" 2>/dev/null | grep -q "OUT_OF_RANGE" && {
        echo ""
        echo "⛔ [CONFORMANCE] regime_snapshot.json 검증 실패"
        echo "   필드: confidence = $CONFIDENCE"
        echo "   허용범위: 0.0 ~ 1.0"
        VIOLATIONS=$((VIOLATIONS + 1))
      }
    fi

    for FIELD in "regime" "confidence" "regime_date" "key_indicators"; do
      if [ "$(field_exists $FIELD)" = "no" ]; then
        echo ""
        echo "⚠️  [CONFORMANCE] regime_snapshot.json 누락 필드: $FIELD"
      fi
    done
    ;;

  risk_assessment.json)
    RISK_GRADE=$(json_get "risk_grade")
    VALID_GRADES="LOW MEDIUM HIGH CRITICAL"

    if ! echo "$VALID_GRADES" | grep -qw "$RISK_GRADE"; then
      echo ""
      echo "⛔ [CONFORMANCE] risk_assessment.json 검증 실패"
      echo "   필드: risk_grade = \"$RISK_GRADE\""
      echo "   허용값: LOW | MEDIUM | HIGH | CRITICAL"
      echo "   조치: INTENT.md 리스크 등급 매트릭스 기준으로 재작성하라"
      VIOLATIONS=$((VIOLATIONS + 1))
    fi

    for FIELD in "risk_grade" "alert" "var_95" "cvar_95"; do
      if [ "$(field_exists $FIELD)" = "no" ]; then
        echo ""
        echo "⚠️  [CONFORMANCE] risk_assessment.json 누락 필드: $FIELD"
      fi
    done
    ;;

  signal_summary.json)
    SENTIMENT=$(json_get "overall_sentiment")
    VALID_SENTIMENTS="Bullish Bearish Neutral"

    if [ -n "$SENTIMENT" ] && ! echo "$VALID_SENTIMENTS" | grep -qw "$SENTIMENT"; then
      echo ""
      echo "⛔ [CONFORMANCE] signal_summary.json 검증 실패"
      echo "   필드: overall_sentiment = \"$SENTIMENT\""
      echo "   허용값: Bullish | Bearish | Neutral"
      VIOLATIONS=$((VIOLATIONS + 1))
    fi
    ;;

  validation_result.json)
    STATUS=$(json_get "status")
    VALID_STATUSES="PASS FAIL WARN"

    if ! echo "$VALID_STATUSES" | grep -qw "$STATUS"; then
      echo ""
      echo "⛔ [CONFORMANCE] validation_result.json 검증 실패"
      echo "   필드: status = \"$STATUS\""
      echo "   허용값: PASS | FAIL | WARN"
      VIOLATIONS=$((VIOLATIONS + 1))
    fi
    ;;

  research_summary.json)
    SENTIMENT=$(json_get "sentiment")
    VALID_SENTIMENTS="Bullish Bearish Neutral"

    if [ -n "$SENTIMENT" ] && ! echo "$VALID_SENTIMENTS" | grep -qw "$SENTIMENT"; then
      echo ""
      echo "⛔ [CONFORMANCE] research_summary.json 검증 실패"
      echo "   필드: sentiment = \"$SENTIMENT\""
      echo "   허용값: Bullish | Bearish | Neutral"
      VIOLATIONS=$((VIOLATIONS + 1))
    fi
    ;;

esac

# ── 결과 ─────────────────────────────────────────────────────────────────────
if [ $VIOLATIONS -gt 0 ]; then
    echo ""
    echo "총 $VIOLATIONS 개의 스키마 위반이 발견되었습니다."
    echo "파일을 도메인 스키마에 맞게 수정한 후 재저장하십시오."
    echo "허용 값 정의: INTENT.md 도메인 어휘 레지스터 참조"
    exit 1
fi

exit 0
