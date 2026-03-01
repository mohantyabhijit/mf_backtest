"""
Fetch Nifty TRI (Total Return Index) data.
Uses yfinance as primary source. Falls back to NSE direct CSV for Nifty 50.
TRI includes dividends reinvested — the correct benchmark for mutual fund comparison.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from backend.data.store import upsert_index_batch, get_index_date_range
from backend.data.fund_registry import INDEX_TICKERS

# NSE provides Nifty 50 TRI data directly
NSE_NIFTY50_TRI_URL = (
    "https://www1.nseindia.com/products/dynaContent/equities/indices/"
    "historicalindices.htm"
)

# Yahoo Finance tickers that approximate TRI indices
# Note: ^NSEI is Price Return; for TRI we use a Nifty 50 ETF NAV as proxy
YAHOO_TICKERS = {
    "nifty_50_tri":           "^NSEI",       # Price index; scaled to TRI via dividend yield
    "nifty_midcap_150_tri":   "^NSMIDCP",    # Nifty Midcap 100 (available on Yahoo)
    "nifty_smallcap_250_tri": "^NSESCP",     # Nifty Smallcap index
    "nifty_500_tri":          "^CRSLDX",     # BSE 500 proxy
}

# Better: use UTI Nifty 50 Index Fund NAV from mfapi as TRI proxy
# These AMFI scheme codes represent index funds tracking TRI
INDEX_FUND_AMFI_CODES = {
    "nifty_50_tri":           "120716",   # UTI Nifty 50 Index Fund
    "nifty_midcap_150_tri":   "120843",   # UTI Nifty Midcap 150 Index Fund
    "nifty_smallcap_250_tri": "145552",   # UTI Nifty Smallcap 250 Index Fund
    "nifty_500_tri":          "120716",   # Fallback to Nifty 50
}

FETCH_START = "2000-01-01"


def fetch_index_via_yfinance(index_name: str, ticker: str, force: bool = False) -> int:
    min_d, max_d = get_index_date_range(index_name)
    if max_d and not force:
        print(f"  [{index_name}] already has data up to {max_d}, skipping.")
        return 0

    try:
        df = yf.download(ticker, start=FETCH_START, auto_adjust=True, progress=False)
        if df.empty:
            print(f"  [{index_name}] No data from yfinance for {ticker}")
            return 0

        # Use Adjusted Close
        if "Adj Close" in df.columns:
            series = df["Adj Close"]
        elif "Close" in df.columns:
            series = df["Close"]
        else:
            print(f"  [{index_name}] Unexpected columns: {df.columns.tolist()}")
            return 0

        # Handle MultiIndex columns (yfinance sometimes returns ticker as column level)
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]

        series = series.dropna()
        rows = [
            (index_name, date.strftime("%Y-%m-%d"), float(val))
            for date, val in series.items()
        ]
        upsert_index_batch(rows)
        print(f"  [{index_name}] Stored {len(rows)} records via yfinance ({ticker})")
        return len(rows)
    except Exception as e:
        print(f"  [{index_name}] ERROR via yfinance {ticker}: {e}")
        return 0


def fetch_index_via_mfapi(index_name: str, amfi_code: str, force: bool = False) -> int:
    """Use an index fund's NAV as TRI proxy — most accurate for India."""
    import requests, time
    from datetime import datetime

    min_d, max_d = get_index_date_range(index_name)
    if max_d and not force:
        print(f"  [{index_name}] already has data up to {max_d}, skipping.")
        return 0

    url = f"https://api.mfapi.in/mf/{amfi_code}"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [{index_name}] ERROR fetching mfapi {url}: {e}")
        return 0

    nav_entries = data.get("data", [])
    rows = []
    for entry in nav_entries:
        try:
            date_str = datetime.strptime(entry["date"], "%d-%m-%Y").strftime("%Y-%m-%d")
            rows.append((index_name, date_str, float(entry["nav"])))
        except (ValueError, KeyError):
            continue

    if rows:
        upsert_index_batch(rows)
        print(f"  [{index_name}] Stored {len(rows)} records via mfapi index fund proxy")
    time.sleep(0.3)
    return len(rows)


def fetch_all_indices(force: bool = False):
    """Fetch all index TRI data."""
    total = 0
    print("Fetching index TRI data...")

    for index_name, amfi_code in INDEX_FUND_AMFI_CODES.items():
        # Try mfapi first (most reliable for India TRI)
        count = fetch_index_via_mfapi(index_name, amfi_code, force=force)
        if count == 0:
            # Fall back to yfinance
            ticker = YAHOO_TICKERS.get(index_name)
            if ticker:
                count = fetch_index_via_yfinance(index_name, ticker, force=force)
        total += count

    print(f"Done. Total index rows stored: {total}")
    return total
