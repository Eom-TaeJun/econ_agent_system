"""
FRED MCP Server — Federal Reserve Economic Data
.mcp.json에서 "fred-api" 서버로 등록됨

실행: python -m mcp_fred_server
의존성: pip install mcp requests
"""

import json
import os
import sys
from datetime import datetime, timedelta
import requests

# MCP SDK (pip install mcp)
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: mcp 패키지 필요. pip install mcp", file=sys.stderr)
    sys.exit(1)

FRED_BASE = "https://api.stlouisfed.org/fred"
API_KEY = os.environ.get("FRED_API_KEY", "")

app = Server("fred-api")


def fred_get(endpoint: str, params: dict) -> dict:
    """FRED API 공통 호출"""
    if not API_KEY:
        raise ValueError("FRED_API_KEY 환경변수가 설정되지 않았습니다")
    params.update({"api_key": API_KEY, "file_type": "json"})
    r = requests.get(f"{FRED_BASE}/{endpoint}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="fetch_series",
            description="FRED 시계열 데이터 조회. 거시경제 지표(GDP, CPI, 금리 등) 수집에 사용.",
            inputSchema={
                "type": "object",
                "properties": {
                    "series_id": {
                        "type": "string",
                        "description": "FRED 시계열 ID (예: DGS10, CPIAUCSL, FEDFUNDS, UNRATE)"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "조회 시작일 YYYY-MM-DD (기본: 3년 전)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "조회 종료일 YYYY-MM-DD (기본: 오늘)"
                    },
                    "frequency": {
                        "type": "string",
                        "description": "집계 주기: d(일), w(주), m(월), q(분기), a(연)",
                        "enum": ["d", "w", "m", "q", "a"]
                    }
                },
                "required": ["series_id"]
            }
        ),
        Tool(
            name="search_series",
            description="FRED에서 키워드로 시계열 검색.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색 키워드 (예: 'korea gdp', 'unemployment rate')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "최대 결과 수 (기본: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="fetch_yield_curve",
            description="현재 미국 국채 수익률 곡선 전체 조회 (3M, 2Y, 5Y, 10Y, 30Y).",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "기준일 YYYY-MM-DD (기본: 최근 영업일)"
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "fetch_series":
        series_id = arguments["series_id"]
        end = arguments.get("end_date", datetime.today().strftime("%Y-%m-%d"))
        start = arguments.get("start_date", (datetime.today() - timedelta(days=3*365)).strftime("%Y-%m-%d"))
        freq = arguments.get("frequency", "")

        params = {
            "series_id": series_id,
            "observation_start": start,
            "observation_end": end,
        }
        if freq:
            params["frequency"] = freq

        data = fred_get("series/observations", params)
        obs = data.get("observations", [])

        # 결측치 필터링
        valid = [o for o in obs if o["value"] != "."]
        result = {
            "series_id": series_id,
            "count": len(valid),
            "start": valid[0]["date"] if valid else None,
            "end": valid[-1]["date"] if valid else None,
            "latest_value": float(valid[-1]["value"]) if valid else None,
            "latest_date": valid[-1]["date"] if valid else None,
            "observations": [
                {"date": o["date"], "value": float(o["value"])}
                for o in valid[-100:]  # 최근 100개 반환
            ]
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    elif name == "search_series":
        data = fred_get("series/search", {
            "search_text": arguments["query"],
            "limit": arguments.get("limit", 10)
        })
        series_list = [
            {
                "id": s["id"],
                "title": s["title"],
                "frequency": s["frequency"],
                "units": s["units"],
                "last_updated": s["last_updated"]
            }
            for s in data.get("seriess", [])
        ]
        return [TextContent(type="text", text=json.dumps(series_list, ensure_ascii=False))]

    elif name == "fetch_yield_curve":
        maturities = {
            "3M": "DGS3MO",
            "2Y": "DGS2",
            "5Y": "DGS5",
            "10Y": "DGS10",
            "30Y": "DGS30"
        }
        curve = {}
        for label, sid in maturities.items():
            try:
                data = fred_get("series/observations", {
                    "series_id": sid,
                    "sort_order": "desc",
                    "limit": 1
                })
                obs = data.get("observations", [])
                if obs and obs[0]["value"] != ".":
                    curve[label] = float(obs[0]["value"])
            except Exception:
                curve[label] = None

        # 스프레드 계산
        spreads = {}
        if curve.get("10Y") and curve.get("2Y"):
            spreads["10Y-2Y"] = round(curve["10Y"] - curve["2Y"], 3)
        if curve.get("10Y") and curve.get("3M"):
            spreads["10Y-3M"] = round(curve["10Y"] - curve["3M"], 3)

        result = {"yields": curve, "spreads": spreads}
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
