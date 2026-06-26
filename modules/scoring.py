import numpy as np
def safe_num(x, default=None):
    try:
        if x is None: return default
        if isinstance(x, float) and np.isnan(x): return default
        return float(x)
    except Exception: return default

def quality_value_score(ticker, role, moat_score, f):
    ticker = ticker.upper()
    is_etf = "ETF" in str(role).upper() or ticker in {"VOO","VGT","SCHD","QQQ","QQQM","SMH","VYM","VIG"}
    if is_etf:
        base = 82 + (8 if ticker in {"VOO","VGT","QQQM","SMH"} else 5 if ticker in {"SCHD","VYM","VIG"} else 0)
        return min(100, int(0.65*base + 0.35*float(moat_score))), ["ETF role quality", "diversification", "trusted watchlist"]
    score, reasons = 0, []
    pe = safe_num(f.get("forwardPE")) or safe_num(f.get("trailingPE"))
    pb = safe_num(f.get("priceToBook")); debt = safe_num(f.get("debtToEquity"))
    roe = safe_num(f.get("returnOnEquity")); margin = safe_num(f.get("profitMargins"))
    rev = safe_num(f.get("revenueGrowth")); earn = safe_num(f.get("earningsGrowth"))
    fcf = safe_num(f.get("freeCashflow")); div = safe_num(f.get("dividendYield")); payout = safe_num(f.get("payoutRatio"))
    if pe is not None:
        if pe < 18: score += 14; reasons.append("reasonable PE")
        elif pe < 30: score += 9; reasons.append("acceptable PE")
        elif pe < 45: score += 4
        else: score -= 5; reasons.append("expensive PE")
    else: score += 4
    if pb is not None: score += 8 if pb < 3 else 4 if pb < 8 else 0
    if debt is not None:
        if debt < 80: score += 10; reasons.append("manageable debt")
        elif debt < 150: score += 4
        else: score -= 4; reasons.append("high debt")
    if fcf is not None and fcf > 0: score += 12; reasons.append("positive free cash flow")
    if rev is not None:
        if rev > 0.15: score += 13; reasons.append("strong revenue growth")
        elif rev > 0.05: score += 8; reasons.append("positive revenue growth")
        elif rev < 0: score -= 6; reasons.append("negative revenue growth")
    if earn is not None:
        if earn > 0.15: score += 10; reasons.append("strong earnings growth")
        elif earn > 0.03: score += 5
    if margin is not None:
        if margin > 0.20: score += 12; reasons.append("high profit margin")
        elif margin > 0.10: score += 8
        elif margin < 0: score -= 8
    if roe is not None:
        if roe > 0.20: score += 12; reasons.append("strong ROE")
        elif roe > 0.10: score += 7
    score += max(0, min(20, float(moat_score)*0.20))
    if float(moat_score) >= 90: reasons.append("high moat/trust score")
    if div is not None and div > 0:
        if payout is not None and payout < 0.75: score += 5; reasons.append("dividend appears supported")
        elif payout is not None and payout > 1: score -= 5; reasons.append("payout ratio risk")
    return int(max(0, min(100, score))), reasons[:6]

def fair_value_range(price, f, role=""):
    eps = safe_num(f.get("forwardEps")) or safe_num(f.get("trailingEps"))
    pe = safe_num(f.get("forwardPE")) or safe_num(f.get("trailingPE"))
    fcf = safe_num(f.get("freeCashflow")); market_cap = safe_num(f.get("marketCap"))
    if "ETF" in str(role).upper() or not eps or eps <= 0:
        return price*0.92, price*1.02, price*1.12, "technical fair-value proxy"
    normal_pe = 22 if pe is None else 15 if pe < 15 else min(28, max(18, pe*0.90)) if pe < 35 else 30
    low, mid, high = eps*normal_pe*0.85, eps*normal_pe, eps*normal_pe*1.15
    if fcf and market_cap and fcf > 0 and market_cap > 0:
        y = fcf/market_cap; adj = 1.05 if y >= .04 else .95 if y < .02 else 1.0
        low *= adj; mid *= adj; high *= adj
    return low, mid, high, "EPS x reasonable PE range"

def final_decision_score(market_score, qv_score, technical_score, kelly_room, trap_count):
    kelly_score = 100 if kelly_room > 0 else 30
    trap_score = max(0, 100 - trap_count*25)
    return int(0.25*market_score + 0.30*qv_score + 0.20*technical_score + 0.15*kelly_score + 0.10*trap_score)
