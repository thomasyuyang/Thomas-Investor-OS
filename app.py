from datetime import date
import pandas as pd
import streamlit as st

from modules.storage import load_positions, save_positions, clean_positions, load_kelly, save_kelly, clean_kelly, load_watchlist, save_watchlist, load_journal, append_journal
from modules.screener import analyze_watchlist
from modules.traps import main_trap_text
from modules.coach import coaching_session, coach_from_journal, render_coach_html
from modules.charts import price_chart

st.set_page_config(page_title="Thomas Investor OS V1.0", page_icon="📈", layout="wide")

st.markdown("""
<style>
.card{background:white;border:1px solid #e5edf5;border-radius:18px;padding:16px 18px;box-shadow:0 2px 12px rgba(0,0,0,0.05);margin:10px 0 16px 0;}
.green{background:#eaf7ef;border-left:7px solid #29a35a}.yellow{background:#fff8e6;border-left:7px solid #d6a300}
.red{background:#fdecec;border-left:7px solid #d94848}.blue{background:#edf2ff;border-left:7px solid #4b6fff}
.title{font-size:1.25rem;font-weight:800;margin-bottom:8px}.line{font-size:1.02rem;line-height:1.55}.small{font-size:.88rem;color:#666}
</style>
""", unsafe_allow_html=True)

def money(x):
    try: return f"${float(x):,.0f}"
    except Exception: return "$0"
def price(x):
    try: return f"${float(x):,.2f}"
    except Exception: return "N/A"
def pct(x):
    try: return f"{float(x):.1f}%"
    except Exception: return "N/A"

with st.sidebar:
    st.header("Thomas Investor OS")
    account = st.number_input("Total investable account value ($)", min_value=1000.0, value=10000.0, step=500.0)
    cash = st.number_input("Cash available ($)", min_value=0.0, value=10000.0, step=100.0)
    min_cash_pct = st.slider("Minimum cash reserve %", 0, 50, 20) / 100
    period = st.selectbox("Research chart period", ["6mo","1y","2y"], index=1)
    if st.button("Refresh live quotes"):
        st.cache_data.clear()
        st.rerun()

st.title("📈 Thomas Investor OS V1.0")
st.caption("Daily capital allocation + investment coaching. Educational decision support only.")

if "positions_df" not in st.session_state: st.session_state.positions_df = load_positions()
if "kelly_df" not in st.session_state: st.session_state.kelly_df = load_kelly()
if "watchlist_df" not in st.session_state: st.session_state.watchlist_df = load_watchlist()

positions = clean_positions(st.session_state.positions_df)
kelly_df = clean_kelly(st.session_state.kelly_df)
watchlist = st.session_state.watchlist_df

pos_map = {r["Ticker"]: {"shares":int(r["Shares"]), "avg_cost":float(r["Avg Cost"])} for _, r in positions.iterrows() if int(r["Shares"]) > 0}
kelly_map = {r["Ticker"]: r for _, r in kelly_df.iterrows()}

with st.spinner("Loading market data and watchlist analysis..."):
    reg, results, details = analyze_watchlist(watchlist, pos_map, kelly_map, account, cash, min_cash_pct, period)

usable = results[~results["Action"].astype(str).str.contains("ERROR", na=False)].copy() if not results.empty else pd.DataFrame()
buyable = usable[usable["Action"].isin(["BUY / ADD","SMALL BUY"])].sort_values("Final Score", ascending=False) if not usable.empty else pd.DataFrame()
best = buyable.iloc[0].to_dict() if not buyable.empty else (usable.sort_values("Final Score", ascending=False).iloc[0].to_dict() if not usable.empty else {"Ticker":"CASH","Action":"WAIT","Final Score":0,"Traps":[]})
best_traps = best.get("Traps", [])
if not isinstance(best_traps, list): best_traps = []

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Morning Briefing", "Research", "Portfolio", "Watchlist & Settings", "Journal"])

with tab1:
    st.subheader("Morning Investment Briefing")
    st.markdown(
        f'<div class="card {reg["tone"]}"><div class="title">1. Market Status — {reg["name"]}</div>'
        f'<div class="line">Market confidence: <b>{reg["score"]}/100</b><br>Buy-size modifier: <b>{pct(reg["modifier"]*100)}</b></div></div>',
        unsafe_allow_html=True
    )
    best_tone = "green" if best.get("Action") in ["BUY / ADD","SMALL BUY"] else "yellow"
    st.markdown(
        f'<div class="card {best_tone}"><div class="title">2. Today\'s Best Opportunity — {best.get("Ticker","CASH")}</div>'
        f'<div class="line">Action: <b>{best.get("Action","WAIT")}</b><br>'
        f'Final Decision Score: <b>{best.get("Final Score",0)}/100</b><br>'
        f'Current Price: <b>{price(best.get("Price",0))}</b><br>'
        f'Fair Value Range: <b>{price(best.get("Fair Value Low",0))} – {price(best.get("Fair Value High",0))}</b><br>'
        f'Investor Quality Score: <b>{best.get("Quality Score",0)}/100</b><br>'
        f'Kelly Buy: <b>{money(best.get("Buy $",0))}</b> / <b>{int(best.get("Buy Shares",0) or 0)} shares</b><br>'
        f'Reference Stop: <b>{price(best.get("Reference Stop",0))}</b><br>'
        f'<span class="small">Quote: {best.get("Quote Source","")} | {best.get("Quote Time","")}</span></div></div>',
        unsafe_allow_html=True
    )
    personal = coach_from_journal(load_journal())
    session = coaching_session(reg["name"], best, best_traps)
    st.markdown(render_coach_html(session, personal), unsafe_allow_html=True)
    st.markdown(
        f'<div class="card yellow"><div class="title">4. Today\'s Trap</div><div class="line">{main_trap_text(best_traps)}</div></div>',
        unsafe_allow_html=True
    )
    total_position_value = sum([float(x) for x in usable.get("Current Value", pd.Series(dtype=float)).fillna(0)]) if not usable.empty else 0
    st.markdown(
        f'<div class="card blue"><div class="title">5. Portfolio Snapshot</div>'
        f'<div class="line">Cash: <b>{money(cash)}</b><br>'
        f'Current analyzed holdings value: <b>{money(total_position_value)}</b><br>'
        f'Minimum cash reserve: <b>{money(account*min_cash_pct)}</b><br>'
        f'Buying power above reserve: <b>{money(max(0, cash-account*min_cash_pct))}</b></div></div>',
        unsafe_allow_html=True
    )
    with st.expander("Why this recommendation?"):
        st.write("The app combines market regime, Investor Quality Score, fair value, technical setup, Kelly room, and trap checks.")
        st.write("Quality reasons:", best.get("Quality Reasons",""))
        st.write("Technical reasons:", best.get("Technical Reasons",""))
        if best_traps: st.write("Traps:", best_traps)

with tab2:
    st.subheader("Research")
    if usable.empty:
        st.warning("No usable results.")
    else:
        selected = st.selectbox("Select ticker", usable.sort_values("Final Score", ascending=False)["Ticker"].tolist())
        d = details.get(selected, {})
        r = d.get("result", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Final Score", f"{r.get('Final Score',0)}/100")
        c2.metric("Quality", f"{r.get('Quality Score',0)}/100")
        c3.metric("Technical", f"{r.get('Technical Score',0)}/100")
        c4.metric("Action", r.get("Action",""))
        st.markdown(f"""
**Price:** {price(r.get('Price',0))}  
**Fair value range:** {price(r.get('Fair Value Low',0))} – {price(r.get('Fair Value High',0))}  
**Method:** {r.get('FV Method','')}  
**Kelly cap:** {money(r.get('Kelly Cap $',0))}  
**Recommended buy:** {money(r.get('Buy $',0))} / {int(r.get('Buy Shares',0) or 0)} shares  
**Reference stop:** {price(r.get('Reference Stop',0))}
""")
        st.write("Quality reasons:", r.get("Quality Reasons",""))
        st.write("Technical reasons:", r.get("Technical Reasons",""))
        traps = r.get("Traps", [])
        if traps: st.warning(main_trap_text(traps))
        else: st.success("No major trap detected.")
        if "history" in d: st.plotly_chart(price_chart(d["history"].tail(150), selected), use_container_width=True)
        with st.expander("Fundamental data from yfinance"):
            st.json(d.get("fundamentals", {}))

with tab3:
    st.subheader("Portfolio")
    edit = st.data_editor(st.session_state.positions_df, num_rows="dynamic", use_container_width=True, key="positions_editor")
    if st.button("Save positions"):
        st.session_state.positions_df = clean_positions(edit); save_positions(st.session_state.positions_df); st.success("Positions saved.")
    if not usable.empty:
        cols = ["Ticker","Shares Held","Avg Cost","Current Value","Kelly Cap $","Max Cap $","Position Room $","Action","Reference Stop"]
        show = usable[[c for c in cols if c in usable.columns]].copy()
        for c in ["Current Value","Kelly Cap $","Max Cap $","Position Room $"]:
            if c in show.columns: show[c] = show[c].map(money)
        if "Reference Stop" in show.columns: show["Reference Stop"] = show["Reference Stop"].map(price)
        st.dataframe(show, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Watchlist")
    st.info("Keep this list small: about 5 ETFs and 10 trusted companies.")
    wedit = st.data_editor(st.session_state.watchlist_df, num_rows="dynamic", use_container_width=True, key="watch_editor")
    if st.button("Save watchlist"):
        st.session_state.watchlist_df = wedit; save_watchlist(wedit); st.success("Watchlist saved.")
    st.subheader("Kelly assumptions")
    kedit = st.data_editor(st.session_state.kelly_df, num_rows="dynamic", use_container_width=True, key="kelly_editor")
    if st.button("Save Kelly inputs"):
        st.session_state.kelly_df = clean_kelly(kedit); save_kelly(st.session_state.kelly_df); st.success("Kelly inputs saved.")

with tab5:
    st.subheader("Investment Journal")
    with st.form("journal_form"):
        c1, c2, c3, c4 = st.columns(4)
        j_date = c1.date_input("Date", date.today())
        j_ticker = c2.text_input("Ticker", best.get("Ticker","MSFT")).upper()
        j_action = c3.selectbox("Action", ["BUY","ADD","WATCH","TRIM","SELL","REVIEW"])
        j_shares = c4.number_input("Shares", min_value=0.0, value=0.0, step=1.0)
        j_price = st.number_input("Price", min_value=0.0, value=0.0, step=0.01)
        j_reason = st.text_area("Reason")
        j_lesson = st.text_area("Lesson")
        if st.form_submit_button("Save journal entry"):
            append_journal({"Date":str(j_date), "Ticker":j_ticker, "Action":j_action, "Shares":j_shares, "Price":j_price, "Reason":j_reason, "Lesson":j_lesson})
            st.success("Journal saved.")
    journal = load_journal()
    st.dataframe(journal.tail(100).iloc[::-1], use_container_width=True, hide_index=True)
    st.download_button("Download journal CSV", journal.to_csv(index=False), "trade_journal.csv", "text/csv")

st.caption("Educational decision support only. Quotes/fundamentals are best-effort from Yahoo Finance and may be delayed or incomplete. Confirm broker bid/ask before trading.")
