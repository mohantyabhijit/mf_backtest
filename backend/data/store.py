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
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS funds (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            amfi_code   TEXT,
            category    TEXT NOT NULL,   -- large_cap, mid_cap, small_cap, flexi_cap, multi_asset, elss, balanced_advantage, index
            source_type TEXT NOT NULL,   -- mfapi, index
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

        CREATE INDEX IF NOT EXISTS idx_nav_fund_date ON nav_data(fund_id, date);
        CREATE INDEX IF NOT EXISTS idx_index_date ON index_data(index_name, date);
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
