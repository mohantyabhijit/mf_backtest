"""SQLite store for NAV data and fund registry."""
import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "mf_backtest.db"


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize SQLite database with clean, essential schema for MF backtesting."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.executescript("""
        CREATE TABLE IF NOT EXISTS funds (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            amfi_code   TEXT,
            category    TEXT NOT NULL,   -- large_cap, mid_cap, small_cap, flexi_cap, multi_asset, elss, balanced_advantage, index
            source_type TEXT NOT NULL,   -- mfapi, index, bse, jugaad
            launch_date TEXT,
            proxy_fund  TEXT             -- fund to use before launch_date (index fallback)
        );

        CREATE TABLE IF NOT EXISTS nav_data (
            fund_id TEXT NOT NULL,
            date    TEXT NOT NULL,
            nav     REAL NOT NULL,
            PRIMARY KEY (fund_id, date),
            FOREIGN KEY (fund_id) REFERENCES funds(id)
        );

        CREATE TABLE IF NOT EXISTS index_data (
            index_name TEXT NOT NULL,
            date       TEXT NOT NULL,
            value      REAL NOT NULL,
            PRIMARY KEY (index_name, date)
        );

        -- Economic indicators (USD-INR rates, etc.)
        CREATE TABLE IF NOT EXISTS economic_data (
            indicator  TEXT NOT NULL,   -- repo_rate, cpi_inflation, usd_inr, etc.
            date       TEXT NOT NULL,
            value      REAL NOT NULL,
            unit       TEXT,           -- percentage, currency, etc.
            source     TEXT DEFAULT 'manual',
            PRIMARY KEY (indicator, date)
        );

        -- Volatility indices (VIX data for risk analysis)
        CREATE TABLE IF NOT EXISTS volatility_data (
            index_name TEXT NOT NULL,   -- India_VIX, VIX, etc.
            date       TEXT NOT NULL,
            value      REAL NOT NULL,
            source     TEXT DEFAULT 'yfinance',
            PRIMARY KEY (index_name, date)
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_nav_date ON nav_data(date);
        CREATE INDEX IF NOT EXISTS idx_nav_fund ON nav_data(fund_id);
        CREATE INDEX IF NOT EXISTS idx_index_date ON index_data(date);
        CREATE INDEX IF NOT EXISTS idx_economic_date ON economic_data(date);
        CREATE INDEX IF NOT EXISTS idx_volatility_date ON volatility_data(date);
    """)
    conn.commit()
    conn.close()
    print(f"DB initialised at {DB_PATH}")


def upsert_fund(fund: dict):
    conn = get_connection()
    conn.execute("""
        INSERT INTO funds (id, name, amfi_code, category, source_type, launch_date, proxy_fund)
        VALUES (:id, :name, :amfi_code, :category, :source_type, :launch_date, :proxy_fund)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name, amfi_code=excluded.amfi_code,
            category=excluded.category, launch_date=excluded.launch_date,
            proxy_fund=excluded.proxy_fund
    """, fund)
    conn.commit()
    conn.close()


def upsert_nav_batch(rows: list):
    """rows: list of (fund_id, date_str, nav_float)"""
    conn = get_connection()
    conn.executemany("""
        INSERT INTO nav_data (fund_id, date, nav) VALUES (?, ?, ?)
        ON CONFLICT(fund_id, date) DO UPDATE SET nav=excluded.nav
    """, rows)
    conn.commit()
    conn.close()


def upsert_index_batch(rows: list):
    """rows: list of (index_name, date_str, value_float)"""
    conn = get_connection()
    conn.executemany("""
        INSERT INTO index_data (index_name, date, value) VALUES (?, ?, ?)
        ON CONFLICT(index_name, date) DO UPDATE SET value=excluded.value
    """, rows)
    conn.commit()
    conn.close()


def get_nav_series(fund_id: str, start: str = None, end: str = None) -> list:
    conn = get_connection()
    q = "SELECT date, nav FROM nav_data WHERE fund_id = ?"
    params = [fund_id]
    if start:
        q += " AND date >= ?"; params.append(start)
    if end:
        q += " AND date <= ?"; params.append(end)
    q += " ORDER BY date"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_index_series(index_name: str, start: str = None, end: str = None) -> list:
    conn = get_connection()
    q = "SELECT date, value FROM index_data WHERE index_name = ?"
    params = [index_name]
    if start:
        q += " AND date >= ?"; params.append(start)
    if end:
        q += " AND date <= ?"; params.append(end)
    q += " ORDER BY date"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_funds() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM funds ORDER BY category, name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_fund(fund_id: str) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM funds WHERE id = ?", (fund_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_nav_date_range(fund_id: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT MIN(date) as min_d, MAX(date) as max_d FROM nav_data WHERE fund_id = ?",
        (fund_id,)
    ).fetchone()
    conn.close()
    return (row["min_d"], row["max_d"]) if row else (None, None)


def get_index_date_range(index_name: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT MIN(date) as min_d, MAX(date) as max_d FROM index_data WHERE index_name = ?",
        (index_name,)
    ).fetchone()
    conn.close()
    return (row["min_d"], row["max_d"]) if row else (None, None)


# New helper functions for extended data
def upsert_bse_stock_batch(rows: list):
    """rows: list of (symbol, date, open, high, low, close, volume, value)"""
    conn = get_connection()
    conn.executemany("""
        INSERT INTO bse_stock_data (symbol, date, open, high, low, close, volume, value) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, date) DO UPDATE SET 
            open=excluded.open, high=excluded.high, low=excluded.low, 
            close=excluded.close, volume=excluded.volume, value=excluded.value
    """, rows)
    conn.commit()
    conn.close()


def upsert_derivatives_batch(rows: list):
    """rows: list of (symbol, expiry, date, instrument, strike, option_type, open, high, low, close, volume, oi)"""
    conn = get_connection()
    conn.executemany("""
        INSERT INTO derivatives_data 
        (symbol, expiry, date, instrument, strike, option_type, open, high, low, close, volume, open_interest) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, expiry, date, instrument, strike, option_type) DO UPDATE SET 
            open=excluded.open, high=excluded.high, low=excluded.low, 
            close=excluded.close, volume=excluded.volume, open_interest=excluded.open_interest
    """, rows)
    conn.commit()
    conn.close()


def upsert_economic_data_batch(rows: list):
    """rows: list of (indicator, date, value, unit, source)"""
    conn = get_connection()
    conn.executemany("""
        INSERT INTO economic_data (indicator, date, value, unit, source) 
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(indicator, date) DO UPDATE SET 
            value=excluded.value, unit=excluded.unit, source=excluded.source
    """, rows)
    conn.commit()
    conn.close()


def upsert_volatility_batch(rows: list):
    """rows: list of (index_name, date, value)"""
    conn = get_connection()
    conn.executemany("""
        INSERT INTO volatility_data (index_name, date, value) 
        VALUES (?, ?, ?)
        ON CONFLICT(index_name, date) DO UPDATE SET value=excluded.value
    """, rows)
    conn.commit()
    conn.close()


def get_bse_stock_series(symbol: str, start: str = None, end: str = None) -> list:
    conn = get_connection()
    q = "SELECT date, open, high, low, close, volume FROM bse_stock_data WHERE symbol = ?"
    params = [symbol]
    if start:
        q += " AND date >= ?"; params.append(start)
    if end:
        q += " AND date <= ?"; params.append(end)
    q += " ORDER BY date"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_economic_series(indicator: str, start: str = None, end: str = None) -> list:
    conn = get_connection()
    q = "SELECT date, value, unit FROM economic_data WHERE indicator = ?"
    params = [indicator]
    if start:
        q += " AND date >= ?"; params.append(start)
    if end:
        q += " AND date <= ?"; params.append(end)
    q += " ORDER BY date"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]
