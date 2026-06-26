import pandas as pd
from .market_data import live_quote, history, fundamentals
from .technical import technical_state
from .scoring import quality_value_score, fair_value_range, final_decision_score
from .portfolio import allocation_result
from .traps import detect_traps

def market_regime():
    total, rows = 0, []
    for t in ["SPY","QQQ","SMH"]:
        try:
            q = live_quote(t)
            hist = history(t, "1y")
            tech, _ = technical_state(hist, t, q["price"])
            score = int(tech["Price"] > tech["EMA50"]) + int(tech["Price"] > tech["EMA200"]) + int(tech["EMA50"] > tech["EMA200"]) + int(tech["RSI"] >= 45)
            total += score
            rows.append({"Ticker":t,"Price":tech["Price"],"Score":score,"RSI":tech["RSI"],"Quote":q["source"],"Time":q["time"]})
        except Exception:
            rows.append({"Ticker":t,"Price":None,"Score":0,"RSI":None,"Quote":"Error","Time":""})
    market_score = int(total/12*100)
    if total >= 10: return {"name":"Bullish","score":market_score,"modifier":1.0,"tone":"green","rows":rows}
    if total >= 7: return {"name":"Neutral","score":market_score,"modifier":0.6,"tone":"yellow","rows":rows}
    return {"name":"Defensive","score":market_score,"modifier":0.25,"tone":"red","rows":rows}

def analyze_watchlist(watchlist, positions_map, kelly_map, account, cash, min_cash_pct, period="1y"):
    reg = market_regime()
    results, details = [], {}
    for _, row in watchlist.iterrows():
        ticker = row["Ticker"]; role = row.get("Role", "Watch"); moat = row.get("MoatScore", 80)
        try:
            q = live_quote(ticker)
            hist = history(ticker, period)
            tech, ind = technical_state(hist, ticker, q["price"])
            f = fundamentals(ticker)
            qv_score, qv_reasons = quality_value_score(ticker, role, moat, f)
            fv_low, fv_mid, fv_high, fv_method = fair_value_range(tech["Price"], f, role)
            pos = positions_map.get(ticker, {"shares":0, "avg_cost":0})
            current_value = pos["shares"]*tech["Price"]
            krow = kelly_map.get(ticker, {"Win Rate %":55,"Avg Win %":10,"Avg Loss %":6,"Kelly Fraction":0.25})
            provisional = final_decision_score(reg["score"], qv_score, tech["Technical Score"], 1, 0)
            alloc = allocation_result(ticker, role, tech, krow, account, cash, current_value, reg["modifier"], provisional, min_cash_pct)
            traps = detect_traps(ticker, tech, qv_score, f, current_value, alloc["Kelly Cap $"], role)
            final = final_decision_score(reg["score"], qv_score, tech["Technical Score"], alloc["Position Room $"], len(traps))
            alloc = allocation_result(ticker, role, tech, krow, account, cash, current_value, reg["modifier"], final, min_cash_pct)
            if traps and alloc["Action"] == "BUY / ADD": alloc["Action"] = "SMALL BUY"
            result = {"Ticker":ticker,"Role":role,"Price":tech["Price"],"Market Regime":reg["name"],"Quality Score":qv_score,"Technical Score":tech["Technical Score"],"Final Score":final,"Fair Value Low":fv_low,"Fair Value":fv_mid,"Fair Value High":fv_high,"FV Method":fv_method,"Current Value":current_value,"Shares Held":pos["shares"],"Avg Cost":pos["avg_cost"],"Quote Source":q["source"],"Quote Time":q["time"],"Quality Reasons":"; ".join(qv_reasons),"Technical Reasons":tech["Tech Reasons"],"Traps":traps, **alloc}
            results.append(result)
            details[ticker] = {"result":result,"tech":tech,"history":ind,"fundamentals":f}
        except Exception as e:
            results.append({"Ticker":ticker,"Role":role,"Final Score":0,"Action":f"ERROR: {e}"})
    return reg, pd.DataFrame(results), details
