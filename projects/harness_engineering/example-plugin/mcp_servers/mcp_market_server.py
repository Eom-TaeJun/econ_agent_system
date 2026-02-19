"""
Market Data MCP Server — 시장 가격/지표 데이터
.mcp.json에서 "market-data" 서버로 등록됨

실행: python -m mcp_market_server
의존성: pip install mcp yfinance pykrx
"""

import json
import os
import sys
from datetime import datetime, timedelta

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: mcp 패키지 필요. pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    from pykrx import stock as krx_stock
    from pykrx import bond as krx_bond
except ImportError:
    krx_stock = None
    krx_bond = None

app = Server("market-data")

# 자주 쓰는 티커 별칭
TICKER_ALIASES = {
    "SPX": "^GSPC",
    "VIX": "^VIX",
    "DXY": "DX-Y.NYB",
    "GOLD": "GC=F",
    "OIL": "CL=F",
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "NASDAQ": "^IXIC",
    "KOSPI": "^KS11",
    "KOSDAQ": "^KQ11",
    "USDKRW": "KRW=X",
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_price",
            description="주식/ETF/지수/암호화폐 가격 및 기본 지표 조회.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "티커 심볼 또는 별칭 (예: ^GSPC, VIX, KOSPI, BTC, AAPL)"
                    },
                    "period": {
                        "type": "string",
                        "description": "기간: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd",
                        "default": "1y"
                    }
                },
                "required": ["ticker"]
            }
        ),
        Tool(
            name="get_multi_price",
            description="여러 자산 가격 동시 조회 (크로스에셋 분석용).",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "티커 목록 (예: ['^GSPC', 'VIX', 'GC=F', 'DX-Y.NYB'])"
                    },
                    "period": {
                        "type": "string",
                        "default": "1y"
                    }
                },
                "required": ["tickers"]
            }
        ),
        Tool(
            name="get_kospi_foreign_flow",
            description="KOSPI 외국인 순매수 데이터 조회 (pykrx). 수급 분석 핵심 지표.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "시작일 YYYYMMDD"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "종료일 YYYYMMDD (기본: 오늘)"
                    }
                },
                "required": ["start_date"]
            }
        ),
        Tool(
            name="get_correlation",
            description="여러 자산 간 상관관계 매트릭스 계산.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "티커 목록 (2개 이상)"
                    },
                    "period": {"type": "string", "default": "1y"},
                    "method": {
                        "type": "string",
                        "description": "pearson 또는 spearman",
                        "enum": ["pearson", "spearman"],
                        "default": "pearson"
                    }
                },
                "required": ["tickers"]
            }
        )
    ]


def resolve_ticker(ticker: str) -> str:
    return TICKER_ALIASES.get(ticker.upper(), ticker)


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if not yf:
        return [TextContent(type="text", text="Error: yfinance 미설치. pip install yfinance")]

    if name == "get_price":
        t = resolve_ticker(arguments["ticker"])
        period = arguments.get("period", "1y")
        data = yf.Ticker(t)
        hist = data.history(period=period)

        if hist.empty:
            return [TextContent(type="text", text=f"데이터 없음: {t}")]

        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest
        change_pct = ((latest["Close"] - prev["Close"]) / prev["Close"]) * 100

        result = {
            "ticker": t,
            "period": period,
            "latest_date": hist.index[-1].strftime("%Y-%m-%d"),
            "close": round(float(latest["Close"]), 4),
            "change_pct": round(float(change_pct), 2),
            "high_52w": round(float(hist["Close"].max()), 4),
            "low_52w": round(float(hist["Close"].min()), 4),
            "avg_volume": int(hist["Volume"].mean()),
            "data_points": len(hist),
            "recent_closes": [
                {"date": d.strftime("%Y-%m-%d"), "close": round(float(v), 4)}
                for d, v in list(zip(hist.index, hist["Close"]))[-30:]
            ]
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    elif name == "get_multi_price":
        tickers = [resolve_ticker(t) for t in arguments["tickers"]]
        period = arguments.get("period", "1y")
        data = yf.download(tickers, period=period, auto_adjust=True, progress=False)

        if data.empty:
            return [TextContent(type="text", text="데이터 없음")]

        close = data["Close"] if "Close" in data.columns else data
        result = {}
        for ticker in tickers:
            if ticker in close.columns:
                series = close[ticker].dropna()
                if not series.empty:
                    latest = float(series.iloc[-1])
                    prev = float(series.iloc[-2]) if len(series) > 1 else latest
                    result[ticker] = {
                        "latest": round(latest, 4),
                        "change_pct": round(((latest - prev) / prev) * 100, 2),
                        "ytd_return": round(((latest / float(series.iloc[0])) - 1) * 100, 2)
                    }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    elif name == "get_kospi_foreign_flow":
        if not krx_stock:
            return [TextContent(type="text", text="Error: pykrx 미설치. pip install pykrx")]

        start = arguments["start_date"]
        end = arguments.get("end_date", datetime.today().strftime("%Y%m%d"))
        try:
            df = krx_stock.get_market_trading_volume_by_date(start, end, "KOSPI")
            if df is not None and not df.empty:
                # 외국인 순매수 추출
                recent = df.tail(20)
                result = {
                    "period": f"{start}~{end}",
                    "data": [
                        {
                            "date": str(idx.date()),
                            "foreign_net": int(row.get("외국인", 0))
                        }
                        for idx, row in recent.iterrows()
                    ]
                }
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        except Exception as e:
            return [TextContent(type="text", text=f"pykrx 오류: {e}")]

    elif name == "get_correlation":
        tickers = [resolve_ticker(t) for t in arguments["tickers"]]
        period = arguments.get("period", "1y")
        method = arguments.get("method", "pearson")

        data = yf.download(tickers, period=period, auto_adjust=True, progress=False)
        close = data["Close"] if "Close" in data.columns else data
        returns = close.pct_change().dropna()

        if method == "pearson":
            corr = returns.corr()
        else:
            corr = returns.corr(method="spearman")

        result = {
            "method": method,
            "period": period,
            "matrix": {
                col: {row: round(float(corr.loc[row, col]), 3) for row in corr.index}
                for col in corr.columns
            }
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
