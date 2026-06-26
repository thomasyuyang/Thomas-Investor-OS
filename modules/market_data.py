from datetime import datetime
import numpy as np, pandas as pd, streamlit as st, yfinance as yf

@st.cache_data(ttl=20)
def live_quote(ticker):
    ticker = ticker.upper().strip()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        tk = yf.Ticker(ticker)
        fi = getattr(tk, "fast_info", {}) or {}
        last = fi.get("last_price", None)
        prev = fi.get("previous_close", None)
        if last and last > 0:
            return {"price": float(last), "previous_close": float(prev) if prev else None, "source": "Yahoo fast_info", "time": now}
    except Exception: pass
    try:
        df = yf.download(ticker, period="1d", interval="1m", auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        if not df.empty:
            return {"price": float(df["Close"].iloc[-1]), "previous_close": None, "source": "Yahoo 1-minute", "time": str(df.index[-1])}
    except Exception: pass
    try:
        df = yf.download(ticker, period="5d", interval="1d", auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        if not df.empty:
            return {"price": float(df["Close"].iloc[-1]), "previous_close": None, "source": "Daily fallback", "time": str(df.index[-1])}
    except Exception: pass
    return {"price": np.nan, "previous_close": None, "source": "Unavailable", "time": now}

@st.cache_data(ttl=300)
def history(ticker, period="1y"):
    df = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    return df.dropna()

@st.cache_data(ttl=3600)
def fundamentals(ticker):
    try: info = yf.Ticker(ticker).info or {}
    except Exception: info = {}
    keys = ["trailingPE","forwardPE","priceToBook","debtToEquity","returnOnEquity","profitMargins","revenueGrowth","earningsGrowth","freeCashflow","dividendYield","payoutRatio","marketCap","currentPrice","trailingEps","forwardEps","beta","totalCash","totalDebt"]
    return {k: info.get(k, None) for k in keys}
