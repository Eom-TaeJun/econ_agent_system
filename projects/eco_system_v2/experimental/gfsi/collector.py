"""
experimental/gfsi/collector.py — GFSI 데이터 수집 (v0.3)

5채널 데이터를 무료 API/XLS로 수집한다.
실패 시 fail-soft: 빈 값 반환 + 경고 로그.

데이터 소스:
  - yfinance: BTC-USD, ETH-USD, GC=F, CL=F, ^VIX
  - DefiLlama: TVL + 스테이블코인 시총 (무료, 키 불필요)
  - Caldara & Iacoviello: GPR 일일 XLS (무료, 키 불필요)
  - FRED: USEPUINDXD (EPU 일일), RRPONTSYD (RRP), WTREGEN (TGA) — 키 필요

v0.3 삭제:
  - collect_currency (DXY/JPY): VIX와 동시 반응, 독립 정보 부족
  - collect_sentiment (F&G): 예측력 없음, crypto_vol과 이중반영
"""

from __future__ import annotations

import json
import logging
import tempfile
from datetime import datetime
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)

# GPR 일일 데이터 XLS (Caldara & Iacoviello)
# CSV는 404 — 공식 사이트에서 XLS만 제공 (2026-03 기준)
GPR_XLS_URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls"


def _fetch_json(url: str, timeout: int = 15) -> dict | list | None:
    """URL에서 JSON을 가져온다. 실패 시 None."""
    try:
        req = Request(url, headers={"User-Agent": "eco_system_v2/gfsi"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (URLError, json.JSONDecodeError, OSError) as e:
        logger.warning("fetch failed: %s — %s", url[:80], e)
        return None


def _fetch_bytes(url: str, timeout: int = 30) -> bytes | None:
    """URL에서 바이너리 데이터를 가져온다. 실패 시 None."""
    try:
        req = Request(url, headers={"User-Agent": "eco_system_v2/gfsi"})
        with urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (URLError, OSError) as e:
        logger.warning("fetch failed: %s — %s", url[:80], e)
        return None


def collect_crypto_vol(period: str = "90d") -> dict[str, Any]:
    """채널1: BTC/ETH 변동성 데이터."""
    import yfinance as yf
    import numpy as np

    result: dict[str, Any] = {}

    try:
        btc = yf.download("BTC-USD", period=period, progress=False)
        if btc.empty:
            return {"error": "BTC data empty"}

        closes = btc["Close"].squeeze()
        returns = closes.pct_change().dropna()

        vol_20d = float(returns.tail(20).std() * np.sqrt(365))
        vol_60d = float(returns.tail(60).std() * np.sqrt(365))

        result["btc_price"] = float(closes.iloc[-1])
        result["btc_vol_20d"] = round(vol_20d, 4)
        result["btc_vol_60d"] = round(vol_60d, 4)
        result["btc_vol_ratio"] = round(vol_20d / vol_60d, 4) if vol_60d > 0 else 1.0
        result["btc_return_7d"] = round(
            float((closes.iloc[-1] / closes.iloc[-8] - 1) * 100), 2
        ) if len(closes) >= 8 else 0.0
    except Exception as e:
        logger.warning("BTC collection failed: %s", e)
        result["error_btc"] = str(e)

    try:
        eth = yf.download("ETH-USD", period="30d", progress=False)
        if not eth.empty:
            eth_close = eth["Close"].squeeze()
            btc_short = yf.download("BTC-USD", period="30d", progress=False)["Close"].squeeze()
            ratio = eth_close / btc_short
            result["eth_btc_ratio"] = round(float(ratio.iloc[-1]), 6)
            result["eth_btc_ratio_20d_avg"] = round(float(ratio.tail(20).mean()), 6)
    except Exception as e:
        logger.warning("ETH collection failed: %s", e)

    return result


def collect_stable_flow() -> dict[str, Any]:
    """채널2: 스테이블코인 시총 + DeFi TVL."""
    result: dict[str, Any] = {}

    stables = _fetch_json("https://stablecoins.llama.fi/stablecoins?includePrices=false")
    if stables and "peggedAssets" in stables:
        total_mcap = 0.0
        for coin in stables["peggedAssets"]:
            chains = coin.get("chainCirculating", {})
            for chain_data in chains.values():
                for peg_type in chain_data.values():
                    if isinstance(peg_type, (int, float)):
                        total_mcap += peg_type
        result["stablecoin_total_mcap_b"] = round(total_mcap / 1e9, 2)

    stable_chart = _fetch_json(
        "https://stablecoins.llama.fi/stablecoincharts/all?stablecoin=1"
    )
    if stable_chart and len(stable_chart) >= 7:
        recent = stable_chart[-1]
        week_ago = stable_chart[-8] if len(stable_chart) >= 8 else stable_chart[0]
        try:
            mcap_now = sum(v for v in recent.get("totalCirculating", {}).values()
                          if isinstance(v, (int, float)))
            mcap_7d = sum(v for v in week_ago.get("totalCirculating", {}).values()
                          if isinstance(v, (int, float)))
            if mcap_7d > 0:
                result["stablecoin_mcap_change_7d_pct"] = round(
                    (mcap_now / mcap_7d - 1) * 100, 3
                )
        except (TypeError, KeyError):
            pass

    tvl_data = _fetch_json("https://api.llama.fi/v2/historicalChainTvl")
    if tvl_data and len(tvl_data) >= 7:
        tvl_now = tvl_data[-1].get("tvl", 0)
        tvl_7d = tvl_data[-8].get("tvl", 0) if len(tvl_data) >= 8 else tvl_data[0].get("tvl", 0)
        result["defi_tvl_b"] = round(tvl_now / 1e9, 2)
        if tvl_7d > 0:
            result["defi_tvl_change_7d_pct"] = round(
                (tvl_now / tvl_7d - 1) * 100, 3
            )

    return result


def collect_geo_stress(period: str = "30d") -> dict[str, Any]:
    """채널3: GPR 텍스트 시그널 + 유가·금 가격 프록시.

    v0.3: GPR Index를 primary 시그널로 추가.
    유가·금 동조는 confirmation 역할로 유지.
    """
    import yfinance as yf
    import numpy as np

    result: dict[str, Any] = {}

    # GPR Index (텍스트 기반, primary)
    gpr_data = _fetch_gpr()
    if gpr_data:
        result.update(gpr_data)

    # 유가·금 (가격 기반, confirmation)
    try:
        tickers = yf.download(
            ["GC=F", "CL=F"], period=period, progress=False
        )["Close"]

        if not tickers.empty:
            gold = tickers["GC=F"].dropna()
            oil = tickers["CL=F"].dropna()

            result["gold_price"] = float(gold.iloc[-1])
            result["oil_price"] = float(oil.iloc[-1])

            g_ret = gold.pct_change().dropna().tail(20)
            o_ret = oil.pct_change().dropna().tail(20)
            if len(g_ret) >= 10 and len(o_ret) >= 10:
                common = g_ret.index.intersection(o_ret.index)
                if len(common) >= 10:
                    corr = float(np.corrcoef(
                        g_ret.loc[common].values,
                        o_ret.loc[common].values
                    )[0, 1])
                    result["oil_gold_corr_20d"] = round(corr, 4)

            if len(gold) >= 20:
                gold_ma20 = float(gold.tail(20).mean())
                result["gold_vs_ma20_pct"] = round(
                    (float(gold.iloc[-1]) / gold_ma20 - 1) * 100, 2
                )

            if len(oil) >= 8:
                result["oil_change_7d_pct"] = round(
                    (float(oil.iloc[-1]) / float(oil.iloc[-8]) - 1) * 100, 2
                )
    except Exception as e:
        logger.warning("Geo stress price collection failed: %s", e)

    return result


def _fetch_gpr() -> dict[str, Any] | None:
    """GPR (Geopolitical Risk) Index 최신 값 가져오기.

    Source: Caldara & Iacoviello (2022), Fed Board of Governors.
    XLS 형식, 일일 업데이트. 무료, 키 불필요.
    역사적 평균 ~100, 위기시 200-500.

    컬럼: DAY, N10D, GPRD, GPRD_ACT, GPRD_THREAT, date, GPRD_MA30, GPRD_MA7
    GPRD = 일일 GPR Index (primary)
    """
    import xlrd

    data = _fetch_bytes(GPR_XLS_URL)
    if not data or len(data) < 1000:
        logger.warning("GPR XLS fetch failed")
        return None

    try:
        # xlrd는 파일 경로 또는 file_contents 지원
        wb = xlrd.open_workbook(file_contents=data)
        sh = wb.sheet_by_index(0)

        if sh.nrows < 10:
            return None

        # 헤더에서 GPRD 컬럼 인덱스 찾기
        headers = [str(sh.cell_value(0, c)).strip() for c in range(sh.ncols)]
        gprd_col = headers.index("GPRD") if "GPRD" in headers else None
        if gprd_col is None:
            logger.warning("GPR XLS: GPRD column not found. Headers: %s", headers)
            return None

        # 최신 행
        gpr_value = float(sh.cell_value(sh.nrows - 1, gprd_col))
        result: dict[str, Any] = {"gpr_current": round(gpr_value, 2)}

        # 최신 날짜 (DAY 컬럼, 형식: YYYYMMDD)
        day_col = headers.index("DAY") if "DAY" in headers else None
        if day_col is not None:
            result["gpr_date"] = str(int(sh.cell_value(sh.nrows - 1, day_col)))

        # 7일 전 GPR
        if sh.nrows >= 9:
            gpr_7d = float(sh.cell_value(sh.nrows - 8, gprd_col))
            result["gpr_7d_ago"] = round(gpr_7d, 2)
            result["gpr_change_7d"] = round(gpr_value - gpr_7d, 2)

        # 30일 평균
        if sh.nrows >= 31:
            recent_30 = [
                float(sh.cell_value(r, gprd_col))
                for r in range(sh.nrows - 30, sh.nrows)
            ]
            result["gpr_30d_avg"] = round(sum(recent_30) / len(recent_30), 2)

        logger.info("GPR fetched: %.1f (date: %s)", gpr_value, result.get("gpr_date", "?"))
        return result
    except Exception as e:
        logger.warning("GPR XLS parsing failed: %s", e)
        return None


def collect_news_stress(fred_api_key: str | None = None) -> dict[str, Any]:
    """채널4: EPU (Economic Policy Uncertainty) Index.

    Source: Baker, Bloom & Davis. FRED 시리즈 USEPUINDXD (일일).
    역사적 평균 ~100-130. 위기시 300-600.
    """
    result: dict[str, Any] = {}

    if not fred_api_key:
        result["note"] = "FRED_API_KEY not set — EPU channel uses fallback"
        return result

    epu = _fetch_json(
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id=USEPUINDXD&api_key={fred_api_key}"
        f"&file_type=json&sort_order=desc&limit=60"
    )
    if epu and "observations" in epu:
        obs = [o for o in epu["observations"] if o.get("value", ".") != "."]
        if obs:
            result["epu_current"] = round(float(obs[0]["value"]), 2)
            result["epu_date"] = obs[0].get("date", "")

            if len(obs) >= 7:
                epu_7d = float(obs[6]["value"])
                result["epu_7d_ago"] = round(epu_7d, 2)
                result["epu_change_7d"] = round(
                    result["epu_current"] - epu_7d, 2
                )

            if len(obs) >= 30:
                recent_30 = [float(o["value"]) for o in obs[:30]]
                result["epu_30d_avg"] = round(sum(recent_30) / len(recent_30), 2)

    return result


def collect_liquidity(fred_api_key: str | None = None) -> dict[str, Any]:
    """채널5: Fed 유동성 지표 (RRP + TGA)."""
    result: dict[str, Any] = {}

    if not fred_api_key:
        result["note"] = "FRED_API_KEY not set — liquidity channel skipped"
        return result

    # RRP
    rrp = _fetch_json(
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id=RRPONTSYD&api_key={fred_api_key}"
        f"&file_type=json&sort_order=desc&limit=30"
    )
    if rrp and "observations" in rrp:
        obs = [o for o in rrp["observations"] if o.get("value", ".") != "."]
        if obs:
            rrp_now = float(obs[0]["value"]) / 1e3  # billions
            result["rrp_current_b"] = round(rrp_now, 2)
            if len(obs) >= 7:
                rrp_7d = float(obs[6]["value"]) / 1e3
                result["rrp_change_7d_abs_b"] = round(rrp_now - rrp_7d, 2)
                if rrp_7d > 0:
                    result["rrp_change_7d_pct"] = round(
                        (rrp_now / rrp_7d - 1) * 100, 2
                    )

    # TGA
    tga = _fetch_json(
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id=WTREGEN&api_key={fred_api_key}"
        f"&file_type=json&sort_order=desc&limit=10"
    )
    if tga and "observations" in tga:
        obs = [o for o in tga["observations"] if o.get("value", ".") != "."]
        if obs:
            result["tga_current_b"] = round(float(obs[0]["value"]) / 1e3, 2)

    return result


def collect_vix() -> dict[str, Any]:
    """비교 기준: 현재 VIX."""
    import yfinance as yf

    try:
        vix = yf.download("^VIX", period="5d", progress=False)["Close"].squeeze()
        if not vix.empty:
            return {"vix_current": float(vix.iloc[-1])}
    except Exception as e:
        logger.warning("VIX collection failed: %s", e)
    return {}


def collect_all(fred_api_key: str | None = None) -> dict[str, dict]:
    """전체 채널 데이터 수집 (v0.3: 5채널)."""
    logger.info("GFSI v0.3: collecting 5 channels...")

    return {
        "crypto_vol": collect_crypto_vol(),
        "stable_flow": collect_stable_flow(),
        "geo_stress": collect_geo_stress(),
        "news_stress": collect_news_stress(fred_api_key),
        "liquidity": collect_liquidity(fred_api_key),
        "vix": collect_vix(),
        "collected_at": datetime.now().isoformat(),
    }
