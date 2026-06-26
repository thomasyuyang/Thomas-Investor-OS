import numpy as np, pandas as pd

def rsi(series, period=14):
    delta = series.diff()
    gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - 100/(1+rs)

def atr(df, period=14):
    tr = pd.concat([df["High"]-df["Low"], (df["High"]-df["Close"].shift()).abs(), (df["Low"]-df["Close"].shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

def indicators(df):
    out = df.copy()
    out["EMA20"] = out["Close"].ewm(span=20, adjust=False).mean()
    out["EMA50"] = out["Close"].ewm(span=50, adjust=False).mean()
    out["EMA200"] = out["Close"].ewm(span=200, adjust=False).mean()
    out["RSI14"] = rsi(out["Close"])
    out["ATR14"] = atr(out)
    out["ATR_PCT"] = out["ATR14"]/out["Close"]*100
    out["HIGH_6M"] = out["Close"].rolling(126, min_periods=30).max()
    out["DIST_HIGH"] = (out["Close"]/out["HIGH_6M"]-1)*100
    return out

def technical_state(df, ticker, live_price=None):
    ind = indicators(df)
    last = ind.iloc[-1]
    px = float(live_price) if live_price and live_price > 0 else float(last["Close"])
    high_6m = float(last["HIGH_6M"]) if float(last["HIGH_6M"]) > 0 else px
    dist_high = (px/high_6m-1)*100
    score, reasons = 0, []
    for cond, pts, txt in [
        (px > last["EMA200"], 15, "above EMA200"),
        (px > last["EMA50"], 15, "above EMA50"),
        (last["EMA20"] > last["EMA50"], 15, "EMA20 above EMA50"),
        (last["EMA50"] > last["EMA200"], 15, "EMA50 above EMA200")]:
        if cond: score += pts; reasons.append(txt)
    rsi_v, atr_pct = float(last["RSI14"]), float(last["ATR_PCT"])
    if 42 <= rsi_v <= 62: score += 25; reasons.append("healthy RSI")
    elif 62 < rsi_v <= 70: score += 12
    elif rsi_v > 70: score -= 10; reasons.append("overbought")
    if -16 <= dist_high <= -5: score += 15; reasons.append("reasonable pullback")
    elif dist_high > -3: score -= 10; reasons.append("near high")
    if atr_pct <= 3: score += 15
    elif atr_pct <= 5: score += 8
    else: score += 2
    return {"Ticker":ticker,"Price":px,"EMA20":float(last["EMA20"]),"EMA50":float(last["EMA50"]),"EMA200":float(last["EMA200"]),"RSI":rsi_v,"ATR":float(last["ATR14"]),"ATR_PCT":atr_pct,"DIST_HIGH":dist_high,"Technical Score":max(0,min(100,score)),"Tech Reasons":"; ".join(reasons)}, ind
