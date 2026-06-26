from .kelly import kelly_fraction, shares_for
ETF_CAPS = {"VOO":0.35, "VGT":0.25, "SCHD":0.25, "QQQM":0.20, "SMH":0.25}

def max_position_pct(ticker, role=""):
    ticker = ticker.upper()
    if ticker in ETF_CAPS: return ETF_CAPS[ticker]
    if ticker in {"MSFT","GOOGL","COST","V","JNJ"}: return 0.15
    if ticker in {"NVDA","AVGO","TSM"}: return 0.12
    if ticker in {"O","MO"}: return 0.10
    return 0.10

def reference_stop(tech, avg_cost=0, has_position=False):
    px = tech["Price"]
    stop = max(tech["EMA50"]*0.98, px - 2.0*tech["ATR"])
    if has_position and avg_cost > 0 and px > avg_cost*1.10:
        stop = max(stop, tech["EMA20"]*0.98, px - 1.8*tech["ATR"])
    return stop

def level_from_tech(tech):
    if tech["Price"] < tech["EMA50"] or tech["EMA20"] < tech["EMA50"]*0.985: return "Weak / below trend"
    if tech["DIST_HIGH"] > -3 and tech["RSI"] >= 68: return "High price level"
    if tech["DIST_HIGH"] > -3: return "Near high"
    if -16 <= tech["DIST_HIGH"] <= -6: return "Good pullback"
    if tech["DIST_HIGH"] < -16: return "Deep pullback"
    return "Normal"

def allocation_result(ticker, role, tech, krow, account, cash, current_value, market_modifier, final_score, min_cash_pct):
    b, raw, cons = kelly_fraction(krow["Win Rate %"], krow["Avg Win %"], krow["Avg Loss %"], krow["Kelly Fraction"])
    kelly_cap = account * cons
    max_cap = account * max_position_pct(ticker, role)
    room = max(0, min(kelly_cap, max_cap) - current_value)
    reserve_room = max(0, cash - account*min_cash_pct)
    if final_score >= 88:
        base, action = 0.12, "BUY / ADD"
    elif final_score >= 78:
        base, action = 0.06, "SMALL BUY"
    elif final_score >= 65:
        base, action = 0, "WATCH"
    else:
        base, action = 0, "AVOID"
    level = level_from_tech(tech)
    if level in {"High price level", "Near high"} and action == "BUY / ADD":
        action, base = "SMALL BUY", min(base, 0.04)
    if level == "Weak / below trend":
        action, base = ("WATCH" if current_value > 0 else "AVOID"), 0
    rule_buy = account*base*market_modifier
    buy_amt = min(rule_buy, room, reserve_room)
    shares = shares_for(buy_amt, tech["Price"])
    buy_amt = shares*tech["Price"]
    stop = reference_stop(tech, 0, current_value > 0)
    return {"Action":action,"Buy $":buy_amt,"Buy Shares":shares,"Kelly Cap $":kelly_cap,"Max Cap $":max_cap,"Position Room $":room,"Rule Buy $":rule_buy,"Conservative Kelly %":cons*100,"Raw Kelly %":raw*100,"Reward/Risk":b,"Reference Stop":stop,"Level":level}
