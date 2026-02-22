"""
Finance Analysis Harness — Broker MCP Server
=============================================
TastyTrade 브로커 연동 MCP 서버 (tasty-agent 패턴 기반)

기본값: BROKER_DRY_RUN=true (실제 주문 차단, 시뮬레이션만 실행)

도구:
  - get_balances()       — 계좌 잔고·매수여력
  - get_positions()      — 보유 포지션·평가손익
  - get_quotes(symbols)  — 실시간 주가
  - get_greeks(options)  — 옵션 Greeks (δ, γ, θ)
  - place_order(legs)    — 주문 실행 (Dry Run 기본)

Rate limiting: 2 req/s 자동 제한
"""

import asyncio
import json
import os
import time
from typing import Any

import httpx

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("[broker] mcp 패키지 없음 — 스텁 모드로 실행")

# ── 환경변수 ──────────────────────────────────────────────────────────────────
TASTYTRADE_USER = os.environ.get("TASTYTRADE_USER", "")
TASTYTRADE_PASS = os.environ.get("TASTYTRADE_PASS", "")
BROKER_DRY_RUN = os.environ.get("BROKER_DRY_RUN", "true").lower() != "false"

TASTYTRADE_BASE = "https://api.tastytrade.com"

# ── Rate Limiter (2 req/s) ────────────────────────────────────────────────────
_last_request_time: float = 0.0
_MIN_INTERVAL = 0.5  # 500ms = 2 req/s


def _rate_limit() -> None:
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request_time = time.monotonic()


# ── TastyTrade HTTP 클라이언트 ────────────────────────────────────────────────
class TastyTradeClient:
    """TastyTrade API 클라이언트 (동기 래퍼)"""

    def __init__(self) -> None:
        self._session_token: str = ""
        self._account_number: str = ""

    def _headers(self) -> dict:
        return {
            "Authorization": self._session_token,
            "Content-Type": "application/json",
        }

    def authenticate(self) -> bool:
        """세션 토큰 발급"""
        if not TASTYTRADE_USER or not TASTYTRADE_PASS:
            return False
        _rate_limit()
        try:
            resp = httpx.post(
                f"{TASTYTRADE_BASE}/sessions",
                json={"login": TASTYTRADE_USER, "password": TASTYTRADE_PASS},
                timeout=10,
            )
            if resp.status_code == 201:
                data = resp.json()["data"]
                self._session_token = data["session-token"]
                self._account_number = data.get("user", {}).get("username", "")
                return True
        except Exception:
            pass
        return False

    def _get_account_number(self) -> str:
        """계좌 번호 조회"""
        if self._account_number:
            return self._account_number
        _rate_limit()
        resp = httpx.get(
            f"{TASTYTRADE_BASE}/customers/me/accounts",
            headers=self._headers(),
            timeout=10,
        )
        accounts = resp.json()["data"]["items"]
        if accounts:
            self._account_number = accounts[0]["account"]["account-number"]
        return self._account_number

    def get_balances(self) -> dict:
        """계좌 잔고·매수여력 조회"""
        if BROKER_DRY_RUN and not self._session_token:
            return _dry_run_balances()
        _rate_limit()
        acct = self._get_account_number()
        resp = httpx.get(
            f"{TASTYTRADE_BASE}/accounts/{acct}/balances",
            headers=self._headers(),
            timeout=10,
        )
        return resp.json()["data"]

    def get_positions(self) -> list:
        """보유 포지션·평가손익 조회"""
        if BROKER_DRY_RUN and not self._session_token:
            return _dry_run_positions()
        _rate_limit()
        acct = self._get_account_number()
        resp = httpx.get(
            f"{TASTYTRADE_BASE}/accounts/{acct}/positions",
            headers=self._headers(),
            timeout=10,
        )
        return resp.json()["data"]["items"]

    def get_quotes(self, symbols: list[str]) -> dict:
        """실시간 주가 조회"""
        if BROKER_DRY_RUN and not self._session_token:
            return _dry_run_quotes(symbols)
        _rate_limit()
        params = {"symbols[]": symbols}
        resp = httpx.get(
            f"{TASTYTRADE_BASE}/market-metrics",
            headers=self._headers(),
            params=params,
            timeout=10,
        )
        items = resp.json()["data"]["items"]
        return {item["symbol"]: item for item in items}

    def get_greeks(self, options: list[str]) -> dict:
        """옵션 Greeks (δ, γ, θ, ν, ρ) 조회"""
        if BROKER_DRY_RUN and not self._session_token:
            return _dry_run_greeks(options)
        _rate_limit()
        params = {"symbols[]": options}
        resp = httpx.get(
            f"{TASTYTRADE_BASE}/option-chains/greeks",
            headers=self._headers(),
            params=params,
            timeout=10,
        )
        return resp.json()["data"]

    def place_order(self, legs: list[dict], dry_run: bool = True) -> dict:
        """
        주문 실행
        legs: [{"instrument-type": "Equity", "symbol": "SPY", "quantity": 1,
                "action": "Buy to Open"}]
        dry_run=True이면 실제 체결 없이 시뮬레이션만 수행
        """
        if BROKER_DRY_RUN or dry_run:
            return _dry_run_order(legs)
        _rate_limit()
        acct = self._get_account_number()
        payload = {
            "time-in-force": "Day",
            "order-type": "Market",
            "legs": legs,
        }
        resp = httpx.post(
            f"{TASTYTRADE_BASE}/accounts/{acct}/orders/dry-run",
            headers=self._headers(),
            json=payload,
            timeout=10,
        )
        return resp.json()["data"]


# ── Dry Run 스텁 데이터 ───────────────────────────────────────────────────────
def _dry_run_balances() -> dict:
    return {
        "dry_run": True,
        "cash-balance": "100000.00",
        "buying-power": "200000.00",
        "net-liquidating-value": "150000.00",
        "maintenance-excess": "75000.00",
    }


def _dry_run_positions() -> list:
    return [
        {
            "dry_run": True,
            "symbol": "SPY",
            "instrument-type": "Equity",
            "quantity": "10",
            "average-open-price": "480.00",
            "unrealized-day-gain": "150.00",
        }
    ]


def _dry_run_quotes(symbols: list[str]) -> dict:
    return {
        sym: {
            "dry_run": True,
            "symbol": sym,
            "last": "500.00",
            "bid": "499.95",
            "ask": "500.05",
            "volume": "50000000",
        }
        for sym in symbols
    }


def _dry_run_greeks(options: list[str]) -> dict:
    return {
        "dry_run": True,
        "items": [
            {
                "symbol": opt,
                "delta": "0.45",
                "gamma": "0.02",
                "theta": "-0.15",
                "vega": "0.25",
                "rho": "0.05",
                "implied-volatility": "0.18",
            }
            for opt in options
        ],
    }


def _dry_run_order(legs: list[dict]) -> dict:
    return {
        "dry_run": True,
        "status": "Simulated",
        "legs": legs,
        "estimated-fees": "1.00",
        "message": "BROKER_DRY_RUN=true — 실제 주문이 전송되지 않았습니다.",
    }


# ── MCP 서버 구현 ─────────────────────────────────────────────────────────────
_client = TastyTradeClient()

TOOLS: list[dict] = [
    {
        "name": "get_balances",
        "description": "TastyTrade 계좌 잔고 및 매수여력 조회. BROKER_DRY_RUN=true이면 시뮬레이션 데이터 반환.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_positions",
        "description": "현재 보유 포지션 및 평가손익 조회.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_quotes",
        "description": "실시간 주가 조회. symbols: ['SPY', 'QQQ', ...]",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "조회할 티커 리스트",
                }
            },
            "required": ["symbols"],
        },
    },
    {
        "name": "get_greeks",
        "description": "옵션 Greeks (델타, 감마, 세타, 베가, 로) 조회.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "옵션 심볼 리스트 (OCC 형식, 예: 'SPY240315C00500000')",
                }
            },
            "required": ["options"],
        },
    },
    {
        "name": "place_order",
        "description": "주문 실행. BROKER_DRY_RUN=true(기본)이면 실제 주문 없이 시뮬레이션만 수행.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "legs": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "주문 leg 목록. 예: [{'instrument-type':'Equity','symbol':'SPY','quantity':1,'action':'Buy to Open'}]",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "true이면 시뮬레이션만. 기본값 true (BROKER_DRY_RUN 환경변수가 우선).",
                    "default": True,
                },
            },
            "required": ["legs"],
        },
    },
]


def _call_tool(name: str, arguments: dict) -> Any:
    """도구 실행 디스패처"""
    if name == "get_balances":
        return _client.get_balances()
    elif name == "get_positions":
        return _client.get_positions()
    elif name == "get_quotes":
        return _client.get_quotes(arguments["symbols"])
    elif name == "get_greeks":
        return _client.get_greeks(arguments["options"])
    elif name == "place_order":
        dry = arguments.get("dry_run", True)
        return _client.place_order(arguments["legs"], dry_run=dry)
    else:
        raise ValueError(f"Unknown tool: {name}")


# ── MCP 서버 진입점 ───────────────────────────────────────────────────────────
if MCP_AVAILABLE:
    server = Server("broker")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["inputSchema"],
            )
            for t in TOOLS
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, _call_tool, name, arguments
            )
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]

    async def main() -> None:
        dry_label = "DRY RUN" if BROKER_DRY_RUN else "LIVE"
        print(f"[broker] MCP 서버 시작 ({dry_label} 모드)")
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    if __name__ == "__main__":
        asyncio.run(main())

else:
    # mcp 패키지 없을 때 — 직접 호출 테스트용
    if __name__ == "__main__":
        print("[broker] 스텁 모드 — MCP 없이 도구 테스트")
        print("get_balances:", json.dumps(_client.get_balances(), indent=2))
        print("get_positions:", json.dumps(_client.get_positions(), indent=2))
        print("get_quotes:", json.dumps(_client.get_quotes(["SPY", "QQQ"]), indent=2))
        print("get_greeks:", json.dumps(_client.get_greeks(["SPY240315C00500000"]), indent=2))
        print("place_order:", json.dumps(_client.place_order([{
            "instrument-type": "Equity",
            "symbol": "SPY",
            "quantity": 1,
            "action": "Buy to Open",
        }]), indent=2))
