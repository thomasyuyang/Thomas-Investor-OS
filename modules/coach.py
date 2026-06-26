def coaching_session(market_regime, best, traps):
    ticker = best.get("Ticker", "CASH")
    action = best.get("Action", "WAIT")
    qv = best.get("Quality Score", 0)
    trap_name = traps[0][0] if traps else ""
    if trap_name in {"Do Not Chase", "Kelly Limit Exceeded"} or action in {"WAIT", "AVOID"}:
        return {"author":"Charlie Munger","lesson":"Avoiding obvious mistakes is often more valuable than finding one more idea.","why":f"{ticker} may be attractive long term, but today's setup requires discipline.","mission":"Do not chase. Respect the position-size rule and wait for a cleaner setup.","tone":"yellow"}
    if market_regime == "Defensive":
        return {"author":"Benjamin Graham","lesson":"Margin of safety comes before enthusiasm.","why":"A defensive market means your first job is protecting capital.","mission":"Keep cash, buy small, and require a better discount before committing more.","tone":"red"}
    if qv >= 85 and action in {"BUY / ADD", "SMALL BUY"}:
        return {"author":"Philip Fisher","lesson":"Outstanding businesses are worth owning patiently when price and quality align.","why":f"{ticker} ranks well because business quality, valuation discipline, and entry timing are aligned enough today.","mission":f"Accumulate {ticker} gradually within the Kelly limit. Do not make a single emotional purchase.","tone":"green"}
    return {"author":"Charlie Munger","lesson":"Waiting is not doing nothing; waiting is discipline.","why":"The app does not see a strong enough advantage today.","mission":"Hold cash and review the watchlist. Let the market come to your price.","tone":"blue"}

def coach_from_journal(journal):
    if journal is None or journal.empty:
        return "Start recording every buy/sell decision. The coach becomes more useful as your journal grows."
    recent = journal.tail(10)
    buys = recent[recent["Action"].astype(str).str.upper().str.contains("BUY|ADD", regex=True)]
    if len(buys) >= 5:
        return "Recent journal shows many buy/add decisions. Be careful not to overtrade or exceed Kelly allocation."
    sells = recent[recent["Action"].astype(str).str.upper().str.contains("SELL|TRIM", regex=True)]
    if len(sells) >= 3:
        return "Recent journal shows several sells/trims. Review whether you are harvesting profits or selling winners too early."
    return "Recent journal looks balanced. Keep writing down the reason before every trade."

def render_coach_html(session, personal):
    return f"""
<div class="card {session.get('tone','blue')}">
  <div class="title">📖 Today's Coaching Session — {session.get('author','')}</div>
  <div class="line">
    <b>Today's lesson:</b><br>{session.get('lesson','')}<br><br>
    <b>Why it matters today:</b><br>{session.get('why','')}<br><br>
    <b>Today's mission:</b><br>{session.get('mission','')}<br><br>
    <b>Personal reminder:</b><br>{personal}
  </div>
</div>
"""
