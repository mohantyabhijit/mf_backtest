"""
Volatility data fetcher using yfinance for India VIX and other volatility indices.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta
from backend.data.store import upsert_volatility_batch


def fetch_india_vix_yfinance(start_date: date, end_date: date) -> int:
    """
    Fetch India VIX data using yfinance.
    Note: India VIX symbol on Yahoo Finance is ^INDIAVIX
    """
    try:
        # India VIX ticker on Yahoo Finance
        vix_ticker = "^INDIAVIX"
        
        df = yf.download(vix_ticker, start=start_date.strftime('%Y-%m-%d'), 
                        end=(end_date + timedelta(days=1)).strftime('%Y-%m-%d'), 
                        progress=False)
        
        if df.empty:
            print(f"No India VIX data available from yfinance")
            return 0
        
        # Use Close prices
        if 'Close' in df.columns:
            close_col = df['Close']
        elif 'Adj Close' in df.columns:
            close_col = df['Adj Close']
        else:
            print(f"No suitable price column found in VIX data")
            return 0
        
        # Handle MultiIndex columns (yfinance sometimes returns ticker as column level)
        if isinstance(close_col, pd.DataFrame):
            close_col = close_col.iloc[:, 0]
        
        close_col = close_col.dropna()
        
        rows = []
        for date_idx, vix_value in close_col.items():
            date_str = date_idx.strftime('%Y-%m-%d')
            rows.append(('india_vix', date_str, float(vix_value)))
        
        if rows:
            upsert_volatility_batch(rows)
            print(f"Stored {len(rows)} India VIX records from yfinance")
            return len(rows)
        
        return 0
        
    except Exception as e:
        print(f"ERROR fetching India VIX via yfinance: {e}")
        return 0


def fetch_cboe_vix(start_date: date, end_date: date) -> int:
    """
    Fetch CBOE VIX (US volatility index) for comparison.
    """
    try:
        vix_ticker = "^VIX"
        
        df = yf.download(vix_ticker, start=start_date.strftime('%Y-%m-%d'), 
                        end=(end_date + timedelta(days=1)).strftime('%Y-%m-%d'), 
                        progress=False)
        
        if df.empty:
            print(f"No CBOE VIX data available")
            return 0
        
        close_col = df['Close'] if 'Close' in df.columns else df['Adj Close']
        
        if isinstance(close_col, pd.DataFrame):
            close_col = close_col.iloc[:, 0]
        
        close_col = close_col.dropna()
        
        rows = []
        for date_idx, vix_value in close_col.items():
            date_str = date_idx.strftime('%Y-%m-%d')
            rows.append(('cboe_vix', date_str, float(vix_value)))
        
        if rows:
            upsert_volatility_batch(rows)
            print(f"Stored {len(rows)} CBOE VIX records from yfinance")
            return len(rows)
        
        return 0
        
    except Exception as e:
        print(f"ERROR fetching CBOE VIX via yfinance: {e}")
        return 0


def fetch_all_volatility_data(days_back: int = 365) -> int:
    """
    Fetch all available volatility indices for the specified period.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)
    
    print(f"Fetching volatility data from {start_date} to {end_date}...")
    
    total_records = 0
    
    # Fetch India VIX
    total_records += fetch_india_vix_yfinance(start_date, end_date)
    
    # Fetch CBOE VIX for comparison
    total_records += fetch_cboe_vix(start_date, end_date)
    
    print(f"Total volatility records fetched: {total_records}")
    return total_records


if __name__ == "__main__":
    # Fetch last 2 years of volatility data
    fetch_all_volatility_data(days_back=730)