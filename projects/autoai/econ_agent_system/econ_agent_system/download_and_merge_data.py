import os
import requests
import pandas as pd
from datetime import datetime
import yfinance as yf
from pycoingecko import CoinGeckoAPI

# -----------------------------
# 1. 기본 설정
# -----------------------------
START_DATE = "2015-01-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")

FRED_API_KEY = os.getenv("FRED_API_KEY")  # 환경변수에 FRED API 키 저장해 두기

if FRED_API_KEY is None:
    raise ValueError("FRED_API_KEY environment variable is not set. Please export it in your shell.")

# FRED 시리즈 ID 예시 (원하면 나중에 조정)
FRED_SERIES = {
    "CPI": "CPIAUCSL",        # 소비자물가
    "M2": "M2SL",             # M2 통화량
    "FEDFUNDS": "FEDFUNDS",   # 기준금리
    "UNRATE": "UNRATE",       # 실업률
    "GDP": "GDP",             # 분기 GDP
    "DOLLAR_INDEX": "DTWEXBGS"  # Broad Dollar Index (DXY 근사)
}

YAHOO_SYMBOLS = {
    "SP500": "^GSPC"          # S&P 500
}

# -----------------------------
# 2. FRED 데이터 가져오기
# -----------------------------
def fetch_fred_series(series_id: str, start_date: str = START_DATE, end_date: str = END_DATE) -> pd.Series:
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()["observations"]

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.set_index("date")["value"].sort_index()
    return df

# -----------------------------
# 3. Yahoo Finance 데이터 가져오기
# -----------------------------
def fetch_yahoo_price(symbol: str, start_date: str = START_DATE, end_date: str = END_DATE) -> pd.Series:
    data = yf.download(symbol, start=start_date, end=end_date, auto_adjust=True, progress=False)
    if data.empty:
        raise ValueError(f"No data returned for symbol {symbol}")
    # 종가 사용
    s = data["Close"].copy()
    s.index = pd.to_datetime(s.index)
    s.name = symbol
    return s

# -----------------------------
# 4. Bitcoin price from Yahoo Finance (BTC-USD)
# -----------------------------
def fetch_bitcoin_price(start_date: str = START_DATE, end_date: str = END_DATE) -> pd.Series:
    # BTC-USD 일별 종가 다운로드
    data = yf.download("BTC-USD", start=start_date, end=end_date, auto_adjust=True, progress=False)
    if data.empty:
        raise ValueError("No data returned for BTC-USD from Yahoo Finance")
    s = data["Close"].copy()          # ← Series
    s.index = pd.to_datetime(s.index)
    s.name = "BTC_USD"
    return s 
# -----------------------------
# 5. 월별 주기로 리샘플링 함수
# -----------------------------
def to_monthly(series: pd.Series, how: str = "last") -> pd.Series:
    if how == "mean":
        return series.resample("ME").mean()   # MonthEnd
    else:
        return series.resample("ME").last()

# -----------------------------
# 6. 전체 파이프라인
# -----------------------------
def build_merged_dataset():
    # 1) FRED 변수들
    fred_monthly = {}
    for name, sid in FRED_SERIES.items():
        print(f"Fetching FRED series {name} ({sid})...")
        s = fetch_fred_series(sid)
        # GDP는 분기 데이터라 그대로 월말로 forward-fill
        if name == "GDP":
            s = s.resample("ME").ffill()
        else:
            s = to_monthly(s, how="last")
        fred_monthly[name] = s

    fred_df = pd.DataFrame(fred_monthly)

    # 2) Yahoo Finance (예: S&P 500)
    yahoo_series_list = []
    for name, sym in YAHOO_SYMBOLS.items():
        print(f"Fetching Yahoo symbol {name} ({sym})...")
        s = fetch_yahoo_price(sym)
        s_m = to_monthly(s, how="last")
        s_m.name = name  # 컬럼 이름을 SP500 같이 설정
        yahoo_series_list.append(s_m)

    if yahoo_series_list:
        yahoo_df = pd.concat(yahoo_series_list, axis=1)
    else:
        yahoo_df = pd.DataFrame()
    # 3) Bitcoin (CoinGecko)
    print("Fetching Bitcoin price from CoinGecko...")
    btc_daily = fetch_bitcoin_price()
    btc_monthly = to_monthly(btc_daily, how="last")
    # btc_monthly가 Series면 DataFrame으로 변환
    if isinstance(btc_monthly, pd.Series):
        btc_monthly = btc_monthly.to_frame()

    # 컬럼 이름 정리
    btc_monthly.columns = ["BTC_USD"]

    # 4) 머지
    df = fred_df.join(yahoo_df, how="outer")
    df = df.join(btc_monthly, how="outer")

    # 5) 공통 기간으로 자르기 (옵션)
    df = df.sort_index()
    # 공통 기간으로 맞추고 싶으면 아래 두 줄 활성화
    # first_valid = df.dropna().index.min()
    # last_valid = df.dropna().index.max()
    # df = df.loc[first_valid:last_valid]

    return df

# -----------------------------
# 7. 실행부
# -----------------------------
if __name__ == "__main__":
    print("Building merged economic + crypto dataset...")
    merged = build_merged_dataset()
    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "merged_econ_crypto_monthly.csv")
    merged.to_csv(out_path, index=True)
    print(f"Saved merged dataset to: {out_path}")
