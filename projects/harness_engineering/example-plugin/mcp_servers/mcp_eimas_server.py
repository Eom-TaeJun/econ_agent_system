"""
EIMAS MCP Server — Economic Intelligence Multi-Agent System 연결
.mcp.json에서 "eimas" 서버로 등록됨

이중 모드 (Dual-mode):
  Primary:  EIMAS FastAPI 실행 중 → HTTP 호출 (localhost:8000)
  Fallback: API 꺼져 있음 → outputs/*.json + data/events.db 직접 읽기

실행: python mcp_servers/mcp_eimas_server.py
의존성: pip install mcp requests
"""

import json
import os
import sqlite3
import sys
import glob
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: mcp 패키지 필요. pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# EIMAS 경로 설정
EIMAS_ROOT = Path(os.environ.get(
    "EIMAS_ROOT",
    str(Path(__file__).parent.parent.parent.parent / "autoai" / "eimas")
))
EIMAS_API = os.environ.get("EIMAS_API_URL", "http://localhost:8000")
OUTPUTS_DIR = EIMAS_ROOT / "outputs"
DATA_DIR = EIMAS_ROOT / "data"

app = Server("eimas")


# ============================================================================
# 헬퍼: API vs 파일 이중 모드
# ============================================================================

def _api_get(endpoint: str, params: dict = None) -> Optional[dict]:
    """EIMAS FastAPI 호출. 실패 시 None 반환."""
    if not HAS_REQUESTS:
        return None
    try:
        r = requests.get(f"{EIMAS_API}{endpoint}", params=params, timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _latest_json(pattern: str) -> Optional[dict]:
    """outputs/ 에서 패턴에 맞는 가장 최신 JSON 파일 읽기."""
    files = sorted(glob.glob(str(OUTPUTS_DIR / pattern)), reverse=True)
    if not files:
        return None
    try:
        with open(files[0]) as f:
            return json.load(f)
    except Exception:
        return None


def _eimas_main_result() -> Optional[dict]:
    """최신 EIMAS 분석 결과 로드 (eimas_*.json 우선, real_analysis_result.json 폴백)."""
    # 타임스탬프 있는 파일 먼저
    data = _latest_json("eimas_*.json")
    if data:
        return data
    # 고정 파일 폴백
    fixed = OUTPUTS_DIR / "real_analysis_result.json"
    if fixed.exists():
        try:
            with open(fixed) as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _regime_history() -> list:
    """regime_history.json 읽기."""
    path = OUTPUTS_DIR / "regime_history.json"
    if path.exists():
        try:
            with open(path) as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            pass
    return []


def _query_events_db(query: str, limit: int = 20) -> list:
    """events.db SQLite 쿼리 (읽기 전용)."""
    db_path = DATA_DIR / "events.db"
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query)
        rows = [dict(r) for r in cur.fetchmany(limit)]
        conn.close()
        return rows
    except Exception as e:
        return [{"error": str(e)}]


# ============================================================================
# MCP 도구 정의
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_latest_analysis",
            description=(
                "EIMAS 최신 종합 분석 결과 조회. "
                "레짐, 최종 추천(BULLISH/BEARISH/NEUTRAL), 신뢰도, 리스크 점수, "
                "AI 에이전트 합의 결과를 반환한다. "
                "EIMAS API가 실행 중이면 실시간 조회, 아니면 최신 파일에서 읽는다."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "특정 섹션만 조회: all, regime, recommendation, risk, analysis, strategy",
                        "default": "all"
                    }
                }
            }
        ),
        Tool(
            name="get_regime",
            description=(
                "현재 시장 레짐 조회 (BULLISH/BEARISH/NEUTRAL/SIDEWAYS). "
                "트렌드, 변동성, 신뢰도, 추천 포지션 방향 포함. "
                "EIMAS API /api/regime 엔드포인트를 우선 호출."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "레짐 분석 기준 티커 (기본: SPY)",
                        "default": "SPY"
                    }
                }
            }
        ),
        Tool(
            name="get_regime_history",
            description=(
                "과거 레짐 이력 조회. 레짐 전환 패턴, VIX, RSI, 섹터 로테이션 시그널 포함. "
                "최근 N개 기록을 반환한다."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "반환할 최대 기록 수 (기본: 10)",
                        "default": 10
                    },
                    "regime_filter": {
                        "type": "string",
                        "description": "특정 레짐만 필터 (BULLISH, BEARISH, NEUTRAL 등, 빈값=전체)"
                    }
                }
            }
        ),
        Tool(
            name="get_signals",
            description=(
                "EIMAS 에이전트 합의 시그널 조회. "
                "BUY/SELL/HOLD 컨센서스와 개별 에이전트 시그널, conviction 점수 포함."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "시그널 최대 수 (기본: 10)",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="get_risk_metrics",
            description=(
                "EIMAS 리스크 지표 조회. VaR, CVaR, Sharpe, 최대낙폭, 변동성 포함. "
                "EIMAS API /api/risk 엔드포인트 또는 최신 분석 파일에서 읽는다."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_sector_rotation",
            description=(
                "섹터 로테이션 신호 조회. 경기사이클 위치, 오버웨이트/언더웨이트 섹터, "
                "추천 비중 포함."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="query_events",
            description=(
                "EIMAS events.db에서 이벤트 이력 조회 (읽기 전용). "
                "시장 이벤트, 공시, 레짐 전환 기록 등을 날짜·타입으로 필터링 가능."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "event_type": {
                        "type": "string",
                        "description": "이벤트 타입 필터 (빈값=전체)"
                    },
                    "since_days": {
                        "type": "integer",
                        "description": "최근 N일 내 이벤트 (기본: 30)",
                        "default": 30
                    },
                    "limit": {
                        "type": "integer",
                        "description": "최대 결과 수 (기본: 20)",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="get_ai_report",
            description=(
                "EIMAS AI 에이전트가 생성한 최신 리포트 요약 조회. "
                "에이전트 토론 결과, 합의 내용, 주요 임플리케이션 포함."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "executive_summary | full",
                        "default": "executive_summary"
                    }
                }
            }
        ),
        Tool(
            name="eimas_status",
            description="EIMAS 시스템 상태 확인. API 서버 실행 여부, 최신 분석 타임스탬프, 데이터 파일 존재 여부.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


# ============================================================================
# 도구 실행
# ============================================================================

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:

    # ── eimas_status ──────────────────────────────────────────────────────────
    if name == "eimas_status":
        api_live = _api_get("/health") is not None
        latest_files = sorted(glob.glob(str(OUTPUTS_DIR / "eimas_*.json")), reverse=True)
        result = {
            "api_server": "running" if api_live else "offline",
            "api_url": EIMAS_API,
            "eimas_root": str(EIMAS_ROOT),
            "outputs_dir_exists": OUTPUTS_DIR.exists(),
            "data_dir_exists": DATA_DIR.exists(),
            "events_db_exists": (DATA_DIR / "events.db").exists(),
            "latest_analysis_file": Path(latest_files[0]).name if latest_files else None,
            "regime_history_exists": (OUTPUTS_DIR / "regime_history.json").exists(),
            "mode": "api" if api_live else "file"
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    # ── get_regime ────────────────────────────────────────────────────────────
    elif name == "get_regime":
        ticker = arguments.get("ticker", "SPY")
        # Primary: API
        data = _api_get("/api/regime", {"ticker": ticker})
        if data:
            data["source"] = "api"
            return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False))]
        # Fallback: 최신 분석 파일
        analysis = _eimas_main_result()
        if analysis:
            regime_ctx = analysis.get("regime_context", {})
            result = {
                "source": "file",
                "timestamp": analysis.get("timestamp"),
                "regime": regime_ctx.get("current_regime") or analysis.get("final_recommendation"),
                "confidence": analysis.get("confidence"),
                "risk_score": None,
                "regime_context": regime_ctx,
            }
            # regime_history에서 최신 항목으로 보완
            history = _regime_history()
            if history:
                latest = history[-1]
                result.update({
                    "regime": latest.get("regime", result["regime"]),
                    "confidence": latest.get("confidence", result["confidence"]),
                    "risk_score": latest.get("risk_score"),
                    "vix": latest.get("vix"),
                    "rsi": latest.get("rsi"),
                    "sector_rotation": latest.get("sector_rotation"),
                    "recommendation": latest.get("recommendation"),
                })
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        return [TextContent(type="text", text='{"error": "EIMAS 데이터 없음. API를 실행하거나 분석을 먼저 수행하세요."}')]

    # ── get_regime_history ────────────────────────────────────────────────────
    elif name == "get_regime_history":
        limit = arguments.get("limit", 10)
        regime_filter = arguments.get("regime_filter", "").upper()
        history = _regime_history()
        if regime_filter:
            history = [h for h in history if h.get("regime", "").upper() == regime_filter]
        recent = history[-limit:][::-1]  # 최신 순
        result = {
            "total_records": len(_regime_history()),
            "returned": len(recent),
            "filter": regime_filter or "none",
            "history": recent
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]

    # ── get_signals ───────────────────────────────────────────────────────────
    elif name == "get_signals":
        limit = arguments.get("limit", 10)
        # Primary: API
        data = _api_get("/api/signals", {"limit": limit})
        if data:
            data["source"] = "api"
            return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False))]
        # Fallback: 분석 파일
        analysis = _eimas_main_result()
        if analysis:
            result = {
                "source": "file",
                "timestamp": analysis.get("timestamp"),
                "consensus_action": analysis.get("final_recommendation"),
                "confidence": analysis.get("confidence"),
                "interpretation": analysis.get("interpretation", {}),
                "strategy": analysis.get("strategy", {}),
            }
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]
        return [TextContent(type="text", text='{"error": "EIMAS 시그널 데이터 없음"}')]

    # ── get_latest_analysis ───────────────────────────────────────────────────
    elif name == "get_latest_analysis":
        section = arguments.get("section", "all")
        analysis = _eimas_main_result()
        if not analysis:
            return [TextContent(type="text", text='{"error": "EIMAS 분석 파일 없음. python main.py --full 실행 필요"}')]

        if section == "all":
            # 핵심 필드만 요약 (전체 파일은 너무 큼)
            result = {
                "timestamp": analysis.get("timestamp"),
                "status": analysis.get("status"),
                "final_recommendation": analysis.get("final_recommendation"),
                "confidence": analysis.get("confidence"),
                "executive_summary": analysis.get("executive_summary"),
                "regime_context": analysis.get("regime_context"),
                "risk_score": analysis.get("stages", {}).get("risk_score"),
            }
        elif section == "regime":
            result = analysis.get("regime_context", {})
        elif section == "recommendation":
            result = {
                "final_recommendation": analysis.get("final_recommendation"),
                "confidence": analysis.get("confidence"),
                "executive_summary": analysis.get("executive_summary"),
            }
        elif section == "risk":
            stages = analysis.get("stages", {})
            result = {
                "risk_score": stages.get("risk_score"),
                "methodology": analysis.get("methodology", {}).get("risk"),
            }
        elif section == "analysis":
            result = analysis.get("analysis", {})
        elif section == "strategy":
            result = analysis.get("strategy", {})
        else:
            result = {"error": f"알 수 없는 섹션: {section}. all/regime/recommendation/risk/analysis/strategy 중 선택"}

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]

    # ── get_risk_metrics ──────────────────────────────────────────────────────
    elif name == "get_risk_metrics":
        # Primary: API
        data = _api_get("/api/risk")
        if data:
            data["source"] = "api"
            return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False))]
        # Fallback: 파일
        analysis = _eimas_main_result()
        if analysis:
            stages = analysis.get("stages", {})
            result = {
                "source": "file",
                "timestamp": analysis.get("timestamp"),
                "risk_score": stages.get("risk_score"),
                "abort_reason": analysis.get("abort_reason"),
                "methodology_risk": analysis.get("methodology", {}).get("risk"),
            }
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]
        return [TextContent(type="text", text='{"error": "리스크 데이터 없음"}')]

    # ── get_sector_rotation ───────────────────────────────────────────────────
    elif name == "get_sector_rotation":
        data = _api_get("/api/sectors")
        if data:
            data["source"] = "api"
            return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False))]
        # Fallback: regime_history의 sector_rotation 필드
        history = _regime_history()
        if history:
            latest = history[-1]
            result = {
                "source": "file",
                "timestamp": latest.get("timestamp"),
                "sector_rotation": latest.get("sector_rotation"),
                "note": "상세 섹터 데이터는 EIMAS API 실행 시 조회 가능"
            }
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        return [TextContent(type="text", text='{"error": "섹터 데이터 없음"}')]

    # ── query_events ──────────────────────────────────────────────────────────
    elif name == "query_events":
        event_type = arguments.get("event_type", "")
        since_days = arguments.get("since_days", 30)
        limit = arguments.get("limit", 20)
        since = (datetime.now() - timedelta(days=since_days)).strftime("%Y-%m-%d")

        # events.db 테이블 구조 먼저 확인
        tables = _query_events_db("SELECT name FROM sqlite_master WHERE type='table'", limit=20)
        if not tables or "error" in (tables[0] if tables else {}):
            return [TextContent(type="text", text=json.dumps({"error": "events.db 접근 불가", "db_path": str(DATA_DIR / "events.db")}, ensure_ascii=False))]

        table_names = [t.get("name") for t in tables]
        # 이벤트 테이블 탐색
        event_table = next((t for t in table_names if "event" in t.lower()), None)
        if not event_table:
            return [TextContent(type="text", text=json.dumps({"tables": table_names, "note": "이벤트 테이블 없음. 가용 테이블 목록 반환"}, ensure_ascii=False))]

        # 동적 쿼리 (injection 방지: 파라미터 사용)
        where_clauses = [f"date(timestamp) >= '{since}'"]
        if event_type:
            where_clauses.append(f"event_type = '{event_type}'")
        where = " AND ".join(where_clauses)
        q = f"SELECT * FROM {event_table} WHERE {where} ORDER BY timestamp DESC LIMIT {limit}"
        rows = _query_events_db(q, limit=limit)
        result = {
            "table": event_table,
            "since_days": since_days,
            "event_type_filter": event_type or "all",
            "count": len(rows),
            "events": rows
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]

    # ── get_ai_report ─────────────────────────────────────────────────────────
    elif name == "get_ai_report":
        section = arguments.get("section", "executive_summary")
        # outputs/ai_report_*.json 또는 ai_report_*.md 탐색
        report_files = sorted(glob.glob(str(OUTPUTS_DIR / "ai_report_*.json")), reverse=True)
        if report_files:
            try:
                with open(report_files[0]) as f:
                    report = json.load(f)
                if section == "executive_summary":
                    result = {
                        "source": Path(report_files[0]).name,
                        "timestamp": report.get("timestamp"),
                        "executive_summary": report.get("executive_summary"),
                        "final_recommendation": report.get("final_recommendation"),
                        "confidence": report.get("confidence"),
                    }
                else:
                    result = {"source": Path(report_files[0]).name, **report}
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]
            except Exception as e:
                pass
        # Fallback: 분석 파일의 executive_summary
        analysis = _eimas_main_result()
        if analysis:
            result = {
                "source": "real_analysis_result.json",
                "timestamp": analysis.get("timestamp"),
                "executive_summary": analysis.get("executive_summary"),
                "final_recommendation": analysis.get("final_recommendation"),
                "confidence": analysis.get("confidence"),
            }
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]
        return [TextContent(type="text", text='{"error": "AI 리포트 없음. python main.py --full 실행 필요"}')]

    return [TextContent(type="text", text=f'{{"error": "알 수 없는 도구: {name}"}}')]


# ============================================================================
# 서버 실행
# ============================================================================

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
