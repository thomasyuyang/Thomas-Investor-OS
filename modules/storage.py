from pathlib import Path
import pandas as pd
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
POSITIONS_PATH = DATA_DIR / "positions.csv"
KELLY_PATH = DATA_DIR / "kelly.csv"
WATCHLIST_PATH = DATA_DIR / "watchlist.csv"
JOURNAL_PATH = DATA_DIR / "trade_journal.csv"

def clean_positions(df):
    for c in ["Ticker","Shares","Avg Cost"]:
        if c not in df.columns: df[c] = "" if c == "Ticker" else 0
    out = df[["Ticker","Shares","Avg Cost"]].copy()
    out["Ticker"] = out["Ticker"].astype(str).str.upper().str.strip()
    out["Shares"] = pd.to_numeric(out["Shares"], errors="coerce").fillna(0).astype(int)
    out["Avg Cost"] = pd.to_numeric(out["Avg Cost"], errors="coerce").fillna(0.0)
    return out[out["Ticker"]!=""].drop_duplicates("Ticker", keep="last").reset_index(drop=True)

def clean_kelly(df):
    for c in ["Ticker","Win Rate %","Avg Win %","Avg Loss %","Kelly Fraction"]:
        if c not in df.columns: df[c] = 0
    out = df[["Ticker","Win Rate %","Avg Win %","Avg Loss %","Kelly Fraction"]].copy()
    out["Ticker"] = out["Ticker"].astype(str).str.upper().str.strip()
    for c in ["Win Rate %","Avg Win %","Avg Loss %","Kelly Fraction"]:
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0.0)
    return out[out["Ticker"]!=""].drop_duplicates("Ticker", keep="last").reset_index(drop=True)

def load_csv(path, cols):
    if path.exists(): return pd.read_csv(path)
    df = pd.DataFrame(columns=cols); df.to_csv(path, index=False); return df

def load_positions(): return clean_positions(load_csv(POSITIONS_PATH, ["Ticker","Shares","Avg Cost"]))
def save_positions(df): clean_positions(df).to_csv(POSITIONS_PATH, index=False)
def load_kelly(): return clean_kelly(load_csv(KELLY_PATH, ["Ticker","Win Rate %","Avg Win %","Avg Loss %","Kelly Fraction"]))
def save_kelly(df): clean_kelly(df).to_csv(KELLY_PATH, index=False)

def load_watchlist():
    df = load_csv(WATCHLIST_PATH, ["Ticker","Role","MoatScore"])
    for c, default in [("Ticker",""),("Role","Watch"),("MoatScore",80)]:
        if c not in df.columns: df[c] = default
    df["Ticker"] = df["Ticker"].astype(str).str.upper().str.strip()
    df["MoatScore"] = pd.to_numeric(df["MoatScore"], errors="coerce").fillna(80)
    return df[df["Ticker"]!=""].drop_duplicates("Ticker").reset_index(drop=True)

def save_watchlist(df):
    for c, default in [("Ticker",""),("Role","Watch"),("MoatScore",80)]:
        if c not in df.columns: df[c] = default
    df["Ticker"] = df["Ticker"].astype(str).str.upper().str.strip()
    df["MoatScore"] = pd.to_numeric(df["MoatScore"], errors="coerce").fillna(80)
    df[["Ticker","Role","MoatScore"]].drop_duplicates("Ticker").to_csv(WATCHLIST_PATH, index=False)

def load_journal():
    cols = ["Date","Ticker","Action","Shares","Price","Reason","Lesson"]
    df = load_csv(JOURNAL_PATH, cols)
    for c in cols:
        if c not in df.columns: df[c] = ""
    return df[cols]

def append_journal(row):
    df = load_journal()
    pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(JOURNAL_PATH, index=False)
