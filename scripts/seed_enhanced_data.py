#!/usr/bin/env python3
"""
Enhanced data seeder with multiple sources.
Extends the original seed_data.py to include new data sources.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.data.store import init_db, upsert_fund
from backend.data.fund_registry import FUNDS
from backend.data.fetcher import fetch_all_funds
from backend.data.index_fetcher import fetch_all_indices
from backend.data.enhanced_fetcher import fetch_enhanced_data


def seed_enhanced(force: bool = False):
    print("=" * 60)
    print("MF Backtest — Enhanced Data Seeder")
    print("=" * 60)

    # 1. Init DB schema (including new tables)
    print("\n[1/6] Initialising enhanced database schema...")
    init_db()

    # 2. Insert fund registry
    print(f"\n[2/6] Inserting {len(FUNDS)} funds into registry...")
    for fund in FUNDS:
        upsert_fund(fund)
        print(f"  Registered: {fund['id']} ({fund['category']})")

    # 3. Fetch NAV data from mfapi.in (existing)
    print("\n[3/6] Fetching mutual fund NAV data from mfapi.in...")
    fetch_all_funds(FUNDS, force=force)

    # 4. Fetch index TRI data (existing)
    print("\n[4/6] Fetching index TRI data...")
    fetch_all_indices(force=force)

    # 5. Fetch enhanced data from multiple sources
    print("\n[5/6] Fetching enhanced market data...")
    try:
        fetch_enhanced_data(force=force)
    except Exception as e:
        print(f"  Enhanced data fetch had issues: {e}")
        print("  Continuing with basic data...")

    # 6. Summary
    print("\n[6/6] Data seeding summary...")
    
    # Quick data count check
    import sqlite3
    from backend.data.store import get_connection
    
    conn = get_connection()
    nav_count = conn.execute("SELECT COUNT(*) FROM nav_data").fetchone()[0]
    index_count = conn.execute("SELECT COUNT(*) FROM index_data").fetchone()[0]
    fund_count = conn.execute("SELECT COUNT(*) FROM funds").fetchone()[0]
    econ_count = conn.execute("SELECT COUNT(*) FROM economic_data").fetchone()[0]
    conn.close()
    
    print(f"  Funds registered: {fund_count}")
    print(f"  NAV records: {nav_count}")
    print(f"  Index records: {index_count}")
    print(f"  Economic indicators: {econ_count}")

    print("\n" + "=" * 60)
    print("Enhanced seeding complete!")
    print("Run: python3 -m backend.app")
    print("=" * 60)


if __name__ == "__main__":
    force = "--force" in sys.argv
    seed_enhanced(force=force)