def detect_traps(ticker, tech, qv_score, f, current_value, kelly_cap, role=""):
    traps = []
    if tech["DIST_HIGH"] > -3 and tech["RSI"] >= 65:
        traps.append(("Do Not Chase", "Price is near recent highs and momentum is hot. Wait for a better entry."))
    if tech["Price"] < tech["EMA50"] and tech["EMA20"] < tech["EMA50"]:
        traps.append(("Falling Trend", "Price is below trend. Buying now requires extra caution."))
    pe = f.get("forwardPE") or f.get("trailingPE")
    rev = f.get("revenueGrowth")
    if pe and pe > 50 and (rev is None or rev < 0.15):
        traps.append(("Valuation Trap", "Valuation is high without enough visible growth support."))
    div = f.get("dividendYield"); payout = f.get("payoutRatio")
    if div and div > 0.07 and payout and payout > 1:
        traps.append(("Dividend Trap", "High yield may not be supported by earnings."))
    if kelly_cap > 0 and current_value > kelly_cap * 1.05:
        traps.append(("Kelly Limit Exceeded", "Current position is already above conservative Kelly allocation."))
    if qv_score < 70 and "ETF" not in str(role).upper():
        traps.append(("Quality Risk", "Investor Quality Score is below the preferred threshold."))
    return traps[:4]

def main_trap_text(traps):
    if not traps:
        return "No major trap detected today."
    return f"{traps[0][0]} — {traps[0][1]}"
